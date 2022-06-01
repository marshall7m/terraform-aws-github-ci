<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| terraform | >=0.15.0 |
| aws | >= 3.22 |
| github | >=4.4.0 |

## Providers

| Name | Version |
|------|---------|
| archive | n/a |
| aws | >= 3.22 |
| github | >=4.4.0 |
| local | n/a |
| null | n/a |
| random | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| api\_description | Description for API-Gateway | `string` | `"API used for custom GitHub webhooks"` | no |
| api\_id | Pre-existing AWS API ID to attach resources to. If not specified, a new API will be created and defining var.api\_name will be required | `string` | `null` | no |
| api\_name | Name of API-Gateway to be created | `string` | `"github-webhook"` | no |
| async\_lambda\_invocation | Determines if the backend Lambda function for the API Gateway is invoked asynchronously.<br>If true, the API Gateway REST API method will not return the Lambda results to the client.<br>See for more info: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html | `bool` | `false` | no |
| create\_api | Determines if Terraform module just create the AWS REST API | `bool` | n/a | yes |
| deployment\_triggers | Arbitrary mapping that when changed causes a redeployment of the API | `map(string)` | `{}` | no |
| enable\_api\_cw\_logs | Determines API execution logs should be stored within a Cloudwatch log group | `bool` | `true` | no |
| execution\_arn | Pre-existing AWS API execution ARN that will be allowed to invoke the Lambda function | `string` | `null` | no |
| function\_name | Name of Lambda function | `string` | `"github-webhook-request-validator"` | no |
| github\_secret\_ssm\_description | Github secret SSM parameter description | `string` | `"Secret value for Github Webhooks"` | no |
| github\_secret\_ssm\_key | Key for github secret within AWS SSM Parameter Store | `string` | `"github-webhook-secret"` | no |
| github\_secret\_ssm\_tags | Tags for Github webhook secret SSM parameter | `map(string)` | `{}` | no |
| github\_token\_ssm\_description | Github token SSM parameter description | `string` | `"Github token used to give access to the payload validator function to get file that differ between commits."` | no |
| github\_token\_ssm\_key | AWS SSM Parameter Store key for sensitive Github personal token | `string` | `"github-webhook-validator-token"` | no |
| github\_token\_ssm\_tags | Tags for Github token SSM parameter | `map(string)` | `{}` | no |
| github\_token\_ssm\_value | Registered Github webhook token associated with the Github provider. <br>  If not provided, module looks for pre-existing SSM parameter via `github_token_ssm_key`.<br>  Token needs full `repo` permissions until github creates a repo scoped token with <br>  granular permissions. See thread here: https://github.community/t/can-i-give-read-only-access-to-a-private-repo-from-a-developer-account/441/165<br>  NOTE: The token is only needed for private repositories | `string` | `""` | no |
| includes\_private\_repo | Determines if an AWS System Manager Parameter Store value is needed by the Lambda Function to access private repos | `bool` | n/a | yes |
| lambda\_failure\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function fails | `list(string)` | `[]` | no |
| lambda\_success\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function succeeds | `list(string)` | `[]` | no |
| repos | List of named repos to create github webhooks for and their respective filter groups<br>Params:<br>  `name`: Repository name<br>  `filter_groups`: List of filter groups that the Github event has to meet. The event has to meet all filters of atleast one group in order to succeed. <br>  [<br>    [ (Filter Group)<br>      {<br>        `type`: The type of filter<br>          (<br>            `event` - Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.<br>            `pr_action` - Pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request<br>            `base_ref` - Pull request base ref<br>            `head_ref` - Pull request head ref<br>            `actor_account_id` - Github user IDs<br>            `commit_message` - GitHub event's commit message<br>            `file_path` - File paths of new, modified, or deleted files<br>          )<br>        `pattern`: Regex pattern that is searched for within the related event's payload attributes. For `type` = `event`, use a single Github webhook event and not a regex pattern.<br>        `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched<br>      }<br>    ]<br>  ] | <pre>list(object({<br>    name = string<br>    filter_groups = list(list(object({<br>      type                   = string<br>      pattern                = string<br>      exclude_matched_filter = optional(bool)<br>    })))<br>  }))</pre> | `[]` | no |
| root\_resource\_id | Pre-existing AWS API resource ID associated with the API defined within var.api\_id to be used as the root resource ID for the github API resource | `string` | `null` | no |
| stage\_name | Stage name for the API deployment | `string` | `"prod"` | no |

## Outputs

| Name | Description |
|------|-------------|
| agw\_log\_group\_arn | ARN of the CloudWatch log group associated with the API gateway |
| agw\_log\_group\_name | Name of the CloudWatch log group associated with the API gateway |
| api\_changes\_sha | SHA value of file that contains API-related configurations. Can be used as a trigger for API deployments (see AWS resource: aws\_api\_gateway\_deployment) |
| api\_stage\_name | API stage name |
| deployment\_invoke\_url | API stage's URL |
| function\_arn | ARN of AWS Lambda Function used to validate Github webhook request |
| function\_name | Name of the Lambda Function used to validate Github webhook request |
| github\_token\_ssm\_arn | ARN of the AWS System Manager Parameter Store key used for the sensitive GitHub Token |
| github\_webhook\_invoke\_url | API URL the github webhook will ping |
| lambda\_deps | Package depedency's file configurations for the Lambda Function |
| lambda\_log\_group\_arn | ARN of the CloudWatch log group associated with the Lambda Function |
| lambda\_log\_group\_name | Name of the CloudWatch log group associated with the Lambda Function |
| webhook\_ids | Map of repo webhook IDs |
| webhook\_urls | Map of repo webhook URLs |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

## Features

- Move Lambda webhook validator from Lambda integration to Lambda Authorizer once/if Lambda Authorizers can receive request `method.request.body`. This will open up the Lambda integration for user defined services. See issue: https://stackoverflow.com/questions/47400447/access-post-request-body-from-custom-authorizer-lambda-function

## Tests

## Requirements

- AWS account must have a pre-existing IAM role that allows AWS AGW to write logs to Cloudwatch log groups. See details here: https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-cloudwatch-logs/


# TODO