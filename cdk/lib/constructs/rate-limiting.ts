import { Construct } from "constructs";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Duration } from "aws-cdk-lib";

export interface RateLimitingProps {
  readonly envName: string;
}

export class RateLimiting extends Construct {
  readonly throttleSettings: apigateway.ThrottleSettings;
  readonly usagePlan: apigateway.UsagePlan;

  constructor(scope: Construct, id: string, props: RateLimitingProps) {
    super(scope, id);

    const isProd = props.envName === 'prod';
    
    // Environment-specific throttle settings
    this.throttleSettings = {
      rateLimit: isProd ? 1000 : 100,  // requests per second
      burstLimit: isProd ? 2000 : 200, // burst capacity
    };
  }

  public createUsagePlan(api: apigateway.RestApi, stage: apigateway.Stage): apigateway.UsagePlan {
    this.usagePlan = new apigateway.UsagePlan(this, "UsagePlan", {
      name: `bedrock-chat-usage-plan-${api.node.id}`,
      throttle: this.throttleSettings,
      quota: {
        limit: 10000,
        period: apigateway.Period.DAY,
      },
      apiStages: [{
        api,
        stage,
        throttle: [{
          path: "/*/*",
          method: apigateway.HttpMethod.ANY,
          ...this.throttleSettings,
        }],
      }],
    });

    return this.usagePlan;
  }
}
