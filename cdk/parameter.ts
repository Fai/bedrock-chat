import { BedrockChatParametersInput } from "./lib/utils/parameter-models";

export const bedrockChatParams = new Map<string, BedrockChatParametersInput>();

bedrockChatParams.set("default", {
  bedrockRegion: "us-east-1",
  enableFrontendIpv6: true,
  enableFrontendWaf: true,
  allowedIpV4AddressRanges: ["0.0.0.0/1", "128.0.0.0/1"],
  allowedIpV6AddressRanges: ["::/1", "8000::/1"],
  allowedCountries: ["TH"],
  allowedSignUpEmailDomains: [],
  autoJoinUserGroups: ["CreatingBotAllowed"],
  userPoolDomainPrefix: "",
  identityProviders: [],
  selfSignUpEnabled: true,
  publishedApiAllowedIpV4AddressRanges: ["0.0.0.0/1", "128.0.0.0/1"],
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
      "claude-v3.7-sonnet",
      "amazon-nova-pro",
      "amazon-nova-lite",
  ],  
  tokenValidMinutes: 30,
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
});

bedrockChatParams.set("prod", {
  bedrockRegion: "us-east-1",
  allowedIpV4AddressRanges: ["0.0.0.0/1", "128.0.0.0/1"],
  enableLambdaSnapStart: true,
  enableRagReplicas: true, // Enhanced availability for production
  enableBotStoreReplicas: true, // Enhanced availability for production
});