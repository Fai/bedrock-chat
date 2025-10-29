import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export interface MonitoringProps {
  /**
   * Environment prefix for resource naming
   */
  envPrefix: string;
  
  /**
   * Email address for alerts
   */
  alertEmail?: string;
  
  /**
   * Lambda function ARN to monitor
   */
  lambdaFunctionArn?: string;
  
  /**
   * DynamoDB table names to monitor
   */
  dynamoTableNames?: string[];
  
  /**
   * Enable detailed monitoring
   */
  enableDetailedMonitoring?: boolean;
}

export class Monitoring extends Construct {
  public readonly dashboard: cloudwatch.Dashboard;
  public readonly alertTopic: sns.Topic;

  constructor(scope: Construct, id: string, props: MonitoringProps) {
    super(scope, id);

    // SNS Topic for alerts
    this.alertTopic = new sns.Topic(this, 'AlertTopic', {
      topicName: `${props.envPrefix}AgentCoreAlerts`,
      displayName: 'AgentCore Migration Alerts',
    });

    if (props.alertEmail) {
      this.alertTopic.addSubscription(
        new subscriptions.EmailSubscription(props.alertEmail)
      );
    }

    // CloudWatch Dashboard
    this.dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
      dashboardName: `${props.envPrefix}AgentCoreMigration`,
    });

    // Add Lambda monitoring if provided
    if (props.lambdaFunctionArn) {
      this.addLambdaMonitoring(props.lambdaFunctionArn, props.envPrefix);
    }

    // Add DynamoDB monitoring if provided
    if (props.dynamoTableNames) {
      this.addDynamoMonitoring(props.dynamoTableNames, props.envPrefix);
    }

    // Add AgentCore specific monitoring
    this.addAgentCoreMonitoring(props.envPrefix);
  }

  private addLambdaMonitoring(functionArn: string, envPrefix: string): void {
    const functionName = functionArn.split(':').pop() || 'unknown';

    // Lambda metrics
    const errorRate = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Errors',
      dimensionsMap: { FunctionName: functionName },
      statistic: 'Sum',
    });

    const duration = new cloudwatch.Metric({
      namespace: 'AWS/Lambda',
      metricName: 'Duration',
      dimensionsMap: { FunctionName: functionName },
      statistic: 'Average',
    });

    // Add to dashboard
    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda Error Rate',
        left: [errorRate],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration',
        left: [duration],
        width: 12,
      })
    );

    // Error rate alarm
    new cloudwatch.Alarm(this, 'LambdaErrorAlarm', {
      alarmName: `${envPrefix}Lambda-HighErrorRate`,
      metric: errorRate,
      threshold: 10,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
    }).addAlarmAction(new cdk.aws_cloudwatch_actions.SnsAction(this.alertTopic));
  }

  private addDynamoMonitoring(tableNames: string[], envPrefix: string): void {
    tableNames.forEach((tableName, index) => {
      const throttles = new cloudwatch.Metric({
        namespace: 'AWS/DynamoDB',
        metricName: 'ThrottledRequests',
        dimensionsMap: { TableName: tableName },
        statistic: 'Sum',
      });

      this.dashboard.addWidgets(
        new cloudwatch.GraphWidget({
          title: `DynamoDB Throttles - ${tableName}`,
          left: [throttles],
          width: 6,
        })
      );
    });
  }

  private addAgentCoreMonitoring(envPrefix: string): void {
    // Custom metrics for AgentCore migration
    const agentCoreRequests = new cloudwatch.Metric({
      namespace: 'BedrockChat/AgentCore',
      metricName: 'RequestCount',
      statistic: 'Sum',
    });

    const agentCoreErrors = new cloudwatch.Metric({
      namespace: 'BedrockChat/AgentCore',
      metricName: 'ErrorCount',
      statistic: 'Sum',
    });

    const migrationRatio = new cloudwatch.MathExpression({
      expression: 'agentcore_requests / (agentcore_requests + legacy_requests) * 100',
      usingMetrics: {
        agentcore_requests: agentCoreRequests,
        legacy_requests: new cloudwatch.Metric({
          namespace: 'BedrockChat/Legacy',
          metricName: 'RequestCount',
          statistic: 'Sum',
        }),
      },
      label: 'AgentCore Usage %',
    });

    this.dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Migration Progress',
        left: [migrationRatio],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'AgentCore vs Legacy Requests',
        left: [agentCoreRequests],
        right: [agentCoreErrors],
        width: 12,
      })
    );

    // High error rate alarm
    new cloudwatch.Alarm(this, 'AgentCoreErrorAlarm', {
      alarmName: `${envPrefix}AgentCore-HighErrorRate`,
      metric: agentCoreErrors,
      threshold: 50,
      evaluationPeriods: 2,
    }).addAlarmAction(new cdk.aws_cloudwatch_actions.SnsAction(this.alertTopic));
  }
}
