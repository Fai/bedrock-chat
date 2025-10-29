import { Construct } from "constructs";
import * as cloudwatch from "aws-cdk-lib/aws-cloudwatch";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

export interface MonitoringProps {
  readonly envName: string;
  readonly lambdaFunctions: lambda.Function[];
  readonly dynamoTables: dynamodb.Table[];
  readonly apiGateway: apigateway.RestApi;
}

export class Monitoring extends Construct {
  readonly dashboard: cloudwatch.Dashboard;

  constructor(scope: Construct, id: string, props: MonitoringProps) {
    super(scope, id);

    this.dashboard = new cloudwatch.Dashboard(this, "BedrockChatDashboard", {
      dashboardName: `bedrock-chat-${props.envName}`,
    });

    // API Gateway metrics
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: "API Gateway Requests",
        left: [
          new cloudwatch.Metric({
            namespace: "AWS/ApiGateway",
            metricName: "Count",
            dimensionsMap: { ApiName: props.apiGateway.restApiName },
            statistic: "Sum",
          }),
        ],
        right: [
          new cloudwatch.Metric({
            namespace: "AWS/ApiGateway",
            metricName: "4XXError",
            dimensionsMap: { ApiName: props.apiGateway.restApiName },
            statistic: "Sum",
          }),
          new cloudwatch.Metric({
            namespace: "AWS/ApiGateway",
            metricName: "5XXError",
            dimensionsMap: { ApiName: props.apiGateway.restApiName },
            statistic: "Sum",
          }),
        ],
      })
    );

    // Lambda metrics
    props.lambdaFunctions.forEach((fn, index) => {
      this.dashboard.addWidgets(
        new cloudwatch.GraphWidget({
          title: `Lambda ${fn.functionName}`,
          left: [fn.metricInvocations(), fn.metricDuration()],
          right: [fn.metricErrors(), fn.metricThrottles()],
        })
      );
    });

    // DynamoDB metrics
    props.dynamoTables.forEach((table) => {
      this.dashboard.addWidgets(
        new cloudwatch.GraphWidget({
          title: `DynamoDB ${table.tableName}`,
          left: [
            table.metricConsumedReadCapacityUnits(),
            table.metricConsumedWriteCapacityUnits(),
          ],
          right: [table.metricThrottledRequests()],
        })
      );
    });
  }
}
