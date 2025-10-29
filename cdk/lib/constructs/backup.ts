import { Construct } from "constructs";
import * as backup from "aws-cdk-lib/aws-backup";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as events from "aws-cdk-lib/aws-events";
import { Duration } from "aws-cdk-lib";

export interface BackupProps {
  readonly envName: string;
  readonly tables: dynamodb.Table[];
}

export class Backup extends Construct {
  readonly backupVault: backup.BackupVault;
  readonly backupPlan: backup.BackupPlan;

  constructor(scope: Construct, id: string, props: BackupProps) {
    super(scope, id);

    const isProd = props.envName === 'prod';

    // Create backup vault
    this.backupVault = new backup.BackupVault(this, "BackupVault", {
      backupVaultName: `bedrock-chat-backup-${props.envName}`,
    });

    // Create backup plan with environment-specific retention
    this.backupPlan = new backup.BackupPlan(this, "BackupPlan", {
      backupPlanName: `bedrock-chat-backup-plan-${props.envName}`,
      backupVault: this.backupVault,
    });

    // Add backup rules based on environment
    if (isProd) {
      // Production: Daily backups with 30-day retention
      this.backupPlan.addRule(new backup.BackupPlanRule({
        ruleName: "DailyBackups",
        scheduleExpression: events.Schedule.cron({ hour: "2", minute: "0" }),
        deleteAfter: Duration.days(30),
        moveToColdStorageAfter: Duration.days(7),
      }));
    } else {
      // Development: Weekly backups with 7-day retention
      this.backupPlan.addRule(new backup.BackupPlanRule({
        ruleName: "WeeklyBackups",
        scheduleExpression: events.Schedule.cron({ 
          hour: "2", 
          minute: "0", 
          weekDay: "SUN" 
        }),
        deleteAfter: Duration.days(7),
      }));
    }

    // Add DynamoDB tables to backup selection
    this.backupPlan.addSelection("DynamoDBSelection", {
      resources: props.tables.map(table => backup.BackupResource.fromDynamoDbTable(table)),
      allowRestores: true,
    });
  }
}
