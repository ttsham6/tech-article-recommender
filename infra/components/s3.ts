import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();
const DEFAULT_EMBEDDING_DIMENSION = config.getNumber("embeddingDimension") ?? 1024;

export class S3 extends pulumi.ComponentResource {
  // for knowledge base
  public readonly kbSourceBucket: aws.s3.Bucket;
  public readonly kbVectorBucket: aws.s3.VectorsVectorBucket;
  public readonly kbVectorIndex: aws.s3.VectorsIndex;
  // for runtime
  public readonly artifactBucket: aws.s3.Bucket;

  constructor(
    name: string,
    props: pulumi.Inputs = {},
    opts?: pulumi.ComponentResourceOptions
  ) {
    super("tech-article-recommender:s3:S3Bucket", name, props, opts);

    this.kbSourceBucket = new aws.s3.Bucket(`${name}-source-bucket`, {
      bucketPrefix: "tech-article-recommender-kb-source-",
      forceDestroy: true,
    }, { parent: this });

    this.kbVectorBucket = new aws.s3.VectorsVectorBucket(`${name}-vector-bucket`, {
      vectorBucketName: `${pulumi.getStack()}-tech-article-recommender-vectors`,
      forceDestroy: true,
    }, { parent: this });

    this.kbVectorIndex = new aws.s3.VectorsIndex(`${name}-vector-index`, {
      indexName: "article-index",
      vectorBucketName: this.kbVectorBucket.vectorBucketName,
      dataType: "float32",
      dimension: DEFAULT_EMBEDDING_DIMENSION,
      distanceMetric: "cosine",
      metadataConfiguration: {
        nonFilterableMetadataKeys: ["AMAZON_BEDROCK_METADATA", "AMAZON_BEDROCK_TEXT"]
      }
    }, { parent: this });

    this.artifactBucket = new aws.s3.Bucket(`${name}-artifact-bucket`, {
      bucketPrefix: "tech-article-runtime-artifact-",
      forceDestroy: true,
    }, { parent: this });

    this.registerOutputs({
      kbSourceBucket: this.kbSourceBucket,
      kbVectorBucket: this.kbVectorBucket,
      kbVectorIndex: this.kbVectorIndex,
      artifactBucket: this.artifactBucket,
    });
  }
}
