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
| api\_name | Name of API-Gateway | `string` | `null` | no |
| async\_lambda\_invocation | Determines if the backend Lambda function for the API Gateway is invoked asynchronously.<br>If true, the API Gateway REST API method will not return the Lambda results to the client.<br>See for more info: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html | `bool` | `false` | no |
| create\_github\_token\_ssm\_param | Determines if an AWS System Manager Parameter Store value should be created for the Github token | `bool` | `true` | no |
| function\_name | Name of Lambda function | `string` | `"github-webhook-request-validator"` | no |
| github\_secret\_ssm\_description | Github secret SSM parameter description | `string` | `"Secret value for Github Webhooks"` | no |
| github\_secret\_ssm\_key | Key for github secret within AWS SSM Parameter Store | `string` | `"github-webhook-github-secret"` | no |
| github\_secret\_ssm\_tags | Tags for Github webhook secret SSM parameter | `map(string)` | `{}` | no |
| github\_token\_ssm\_description | Github token SSM parameter description | `string` | `"Github token used to give read access to the payload validator function to get file that differ between commits"` | no |
| github\_token\_ssm\_key | AWS SSM Parameter Store key for sensitive Github personal token | `string` | `"github-webhook-validator-token"` | no |
| github\_token\_ssm\_tags | Tags for Github token SSM parameter | `map(string)` | `{}` | no |
| github\_token\_ssm\_value | Registered Github webhook token associated with the Github provider. If not provided, module looks for pre-existing SSM parameter via `github_token_ssm_key` | `string` | `""` | no |
| lambda\_failure\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function fails | `list(string)` | `[]` | no |
| lambda\_success\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function succeeds | `list(string)` | `[]` | no |
| repos | List of named repos to create github webhooks for and their respective filter groups<br>Params:<br>  `name`: Repository name<br>  `filter_groups`: {<br>    `events` - List of Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.<br>    `pr_actions` - List of pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request<br>    `base_refs` - List of base refs<br>    `head_refs` - List of head refs<br>    `actor_account_ids` - List of Github user IDs<br>    `commit_messages` - List of commit messages<br>    `file_paths` - List of file paths<br>    `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched<br>  } | <pre>list(object({<br>    name = string<br>    filter_groups = optional(list(object({<br>      events                 = list(string)<br>      pr_actions             = optional(list(string))<br>      base_refs              = optional(list(string))<br>      head_refs              = optional(list(string))<br>      actor_account_ids      = optional(list(string))<br>      commit_messages        = optional(list(string))<br>      file_paths             = optional(list(string))<br>      exclude_matched_filter = optional(bool)<br>    })))<br>  }))</pre> | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| cw\_log\_group\_arn | ARN of the CloudWatch log group associated with the Lambda function |
| function\_arn | ARN of AWS Lambda function used to validate Github webhook request |
| function\_name | Name of the Lambda function used to validate Github webhook request |
| github\_token\_ssm\_arn | ARN of the AWS System Manager Parameter Store key used for the sensitive GitHub Token |
| invoke\_url | API invoke URL the github webhook will ping |
| lambda\_deps | Package depedency's file configurations for the Lambda function |
| webhook\_urls | Map of repo webhook URLs |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->