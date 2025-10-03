import { BedrockChatParametersInput } from "./lib/utils/parameter-models";

export const bedrockChatParams = new Map<string, BedrockChatParametersInput>();
// You can define multiple environments and their parameters here

// If you define "default" environment here, parameters in cdk.json are ignored
// bedrockChatParams.set("default", {});
// bedrockChatParams.set("default", {
//   bedrockRegion: "us-east-1",
//   allowedIpV4AddressRanges: ["192.168.0.0/16"],
//   selfSignUpEnabled: true,
//   globalAvailableModels: [
//       "claude-v3.7-sonnet",
//       "claude-v3.5-sonnet",
//       "amazon-nova-pro",
//       "amazon-nova-lite",
//       "llama3-3-70b-instruct"
//     ],
// });

// // Define parameters for additional environments
// // bedrockChatParams.set("dev", {});
// bedrockChatParams.set("dev", {
//   bedrockRegion: "us-west-2",
//   allowedIpV4AddressRanges: ["10.0.0.0/8"],
//   enableRagReplicas: false, // Cost-saving for dev environment
//   enableBotStoreReplicas: false, // Cost-saving for dev environment
// });

// bedrockChatParams.set("prod", {
//   bedrockRegion: "us-east-1",
//   allowedIpV4AddressRanges: ["172.16.0.0/12"],
//   enableLambdaSnapStart: true,
//   enableRagReplicas: true, // Enhanced availability for production
//   enableBotStoreReplicas: true, // Enhanced availability for production
// });