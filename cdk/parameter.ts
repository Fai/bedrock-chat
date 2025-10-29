import { BedrockChatParametersInput } from "./lib/utils/parameter-models";

export const bedrockChatParams = new Map<string, BedrockChatParametersInput>();

bedrockChatParams.set("default", {
  bedrockRegion: "us-east-1",
  enableFrontendIpv6: true,
  enableFrontendWaf: true,
  allowedIpV4AddressRanges: ["10.0.0.0/8", "172.16.0.0/12"], // Restrict to private networks
  allowedIpV6AddressRanges: ["::/1", "8000::/1"],
  allowedCountries: ["TH"],
  allowedSignUpEmailDomains: ["company.com"], // Restrict to company domain
  autoJoinUserGroups: ["CreatingBotAllowed"],
  userPoolDomainPrefix: "",
  identityProviders: [],
  selfSignUpEnabled: false, // Disable self-signup for security
  publishedApiAllowedIpV4AddressRanges: ["10.0.0.0/8", "172.16.0.0/12"],
  publishedApiAllowedIpV6AddressRanges: [
      "0000:0000:0000:0000:0000:0000:0000:0000/1",
      "8000:0000:0000:0000:0000:0000:0000:0000/1"
    ],
  enableRagReplicas: false,
  enableBedrockCrossRegionInference: true,
  enableLambdaSnapStart: true,
  enableBotStore: true,
  enableBotStoreReplicas: false,
  botStoreLanguage: "en",
  globalAvailableModels: [
      "claude-v3-haiku",
      "claude-v3.5-sonnet", 
      "amazon-nova-pro",
      "amazon-nova-lite",
      "amazon-nova-micro"
  ],  
  tokenValidMinutes: 15, // Reduce token validity for security
  alternateDomainName: "",
  hostedZoneId: "",
  enableAuroraKb: false,  // Disabled by default
  auroraKbMinCapacity: 0.5,  // 0.5 ACU minimum
  auroraKbMaxCapacity: 4,    // 4 ACU maximum
  devAccessIamRoleArn: ""
});

bedrockChatParams.set("dev", {
  bedrockRegion: "us-east-1",
  allowedIpV4AddressRanges: ["0.0.0.0/1", "128.0.0.0/1"],
  enableRagReplicas: false, // Cost-saving for dev environment
  enableBotStoreReplicas: false, // Cost-saving for dev environment
  enableAuroraKb: true,  // Enable for development testing
  auroraKbMinCapacity: 0.5,  // Minimum for cost savings
  auroraKbMaxCapacity: 2,    // Lower max for dev
  // AgentCore - Enable for testing Strands agent framework migration
  enableAgentCore: true,
  enableAgentCoreMemory: true,
  enableAgentCoreObservability: true,
});

bedrockChatParams.set("prod", {
  bedrockRegion: "us-east-1",
  allowedIpV4AddressRanges: ["10.0.0.0/8", "172.16.0.0/12"], // Restrict to private networks
  allowedSignUpEmailDomains: ["company.com"], // Company domain only
  selfSignUpEnabled: false, // Disable self-signup in production
  enableLambdaSnapStart: true,
  enableRagReplicas: true, // Enhanced availability for production
  enableBotStoreReplicas: true, // Enhanced availability for production
  tokenValidMinutes: 10, // Shorter token validity in production
});