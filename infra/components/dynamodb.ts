import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const JOB_TABLE_NAME = "tech-article-recommender-jobs";
const TTL_ATTRIBUTE_NAME = "expiresAt";

export class DynamoDb extends pulumi.ComponentResource {
    public readonly jobsTable: aws.dynamodb.Table;

    constructor(
        name: string,
        props: pulumi.Inputs = {},
        opts?: pulumi.ComponentResourceOptions,
    ) {
        super("tech-article-recommender:dynamodb:DynamoDb", name, props, opts);

        this.jobsTable = new aws.dynamodb.Table(`${name}-jobs-table`, {
            name: JOB_TABLE_NAME,
            billingMode: "PAY_PER_REQUEST",
            hashKey: "jobId",
            attributes: [
                {
                    name: "jobId",
                    type: "S",
                },
            ],
            ttl: {
                attributeName: TTL_ATTRIBUTE_NAME,
                enabled: true,
            },
        }, { parent: this });

        this.registerOutputs({
            jobsTableName: this.jobsTable.name,
            jobsTableArn: this.jobsTable.arn,
            ttlAttributeName: TTL_ATTRIBUTE_NAME,
        });
    }
}
