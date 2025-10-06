import { createMachine, assign } from 'xstate';
import { produce } from 'immer';

import { AgentToolsProps, AgentToolState } from '../../features/agent/types';
import { RelatedDocument } from '../../@types/conversation';

export const StreamingState = {
  SLEEPING: 'sleeping',
  STREAMING: 'streaming',
  LEAVING: 'leaving',
} as const;

export type StreamingContext = {
  reasoning: string;
  text: string;
  tools: AgentToolsProps[];
  relatedDocuments: RelatedDocument[];
  areAllToolsSuccessful: boolean;
};

export type StreamingEvent =
  | { type: 'reasoning'; reasoning: string }
  | { type: 'text'; text: string }
  | { type: 'tool-use'; toolUseId: string; name: string; input: object }
  | { type: 'tool-result'; toolUseId: string; status: AgentToolState }
  | { type: 'related-document'; toolUseId: string; relatedDocument: RelatedDocument }
  | { type: 'reset' }
  | { type: 'goodbye' }
  | { type: 'wakeup' };

export const streamingStateMachine = createMachine<StreamingContext, StreamingEvent>({
  id: 'streaming',
  context: {
    reasoning: '',
    text: '',
    tools: [],
    relatedDocuments: [],
    areAllToolsSuccessful: false,
  },
  initial: 'sleeping',
  states: {
    sleeping: {
      on: {
        wakeup: { target: 'streaming' },
        reasoning: { target: 'streaming', actions: 'appendReasoning' },
        text: { target: 'streaming', actions: 'appendText' },
        'tool-use': { target: 'streaming', actions: 'addTool' },
        'tool-result': { actions: 'updateToolResult' },
        'related-document': { actions: 'addRelatedDocument' },
        goodbye: { target: 'leaving' },
      },
    },
    streaming: {
      on: {
        reasoning: { actions: 'appendReasoning' },
        text: { actions: 'appendText' },
        'tool-use': { actions: 'addTool' },
        'tool-result': { actions: 'updateToolResult' },
        'related-document': { actions: 'addRelatedDocument' },
        goodbye: { target: 'leaving' },
      },
    },
    leaving: {
      on: {
        reset: { target: 'sleeping', actions: 'reset' },
      },
    },
  },
}, {
  actions: {
    reset: assign({ reasoning: '', text: '', tools: [], relatedDocuments: [] }),
    appendReasoning: assign({
      reasoning: (context, event) => event.type === 'reasoning' ? context.reasoning + event.reasoning : context.reasoning,
    }),
    appendText: assign({
      text: (context, event) => event.type === 'text' ? context.text + event.text : context.text,
    }),
    addTool: assign((context, event) => produce(context, (draft: any) => {
      if (event.type === 'tool-use') {
        const reasoning = draft.reasoning || undefined;
        const text = draft.text || undefined;
        draft.reasoning = '';
        draft.text = '';
        
        if (draft.tools.length > 0 && !text && !reasoning) {
          draft.tools[draft.tools.length - 1].tools[event.toolUseId] = {
            name: event.name, input: event.input, status: 'running'
          };
        } else {
          draft.tools.push({
            reasoning, thought: text,
            tools: { [event.toolUseId]: { name: event.name, input: event.input, status: 'running' } }
          });
        }
      }
    })),
    updateToolResult: assign({
      tools: (context, event) => produce(context.tools, (draft: any) => {
        if (event.type === 'tool-result') {
          const tool = draft.find((t: any) => event.toolUseId in t.tools);
          if (tool) tool.tools[event.toolUseId].status = event.status;
        }
      }),
    }),
    addRelatedDocument: assign((context, event) => produce(context, (draft: any) => {
      if (event.type === 'related-document') {
        const tool = draft.tools.find((t: any) => event.toolUseId in t.tools);
        if (tool) {
          const toolUse = tool.tools[event.toolUseId];
          toolUse.relatedDocuments = toolUse.relatedDocuments || [];
          toolUse.relatedDocuments.push(event.relatedDocument);
        }
        draft.relatedDocuments.push(event.relatedDocument);
      }
    })),
  },
});
