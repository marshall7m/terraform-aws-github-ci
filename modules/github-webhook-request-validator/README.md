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
| random | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| api\_description | Description for API-Gateway | `string` | `"API used for custom GitHub webhooks"` | no |
| api\_name | Name of API-Gateway | `string` | `null` | no |
| async\_lambda\_invocation | Determines if the backend Lambda function for the API Gateway is invoked asynchronously.<br>If true, the API Gateway REST API method will not return the Lambda results to the client.<br>See for more info: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html | `bool` | `false` | no |
| function\_name | Name of Lambda function | `string` | `"github-webhook-request-validator"` | no |
| github\_secret\_ssm\_description | Github secret SSM parameter description | `string` | `"Secret value for Github Webhooks"` | no |
| github\_secret\_ssm\_key | Key for github secret within AWS SSM Parameter Store | `string` | `"github-webhook-request-validator-github-token"` | no |
| github\_secret\_ssm\_tags | Tags for Github webhook secret SSM parameter | `map(string)` | `{}` | no |
| lambda\_failure\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function fails | `list(string)` | `[]` | no |
| lambda\_success\_destination\_arns | AWS ARNs of services that will be invoked if Lambda function succeeds | `list(string)` | `[]` | no |
| repos | List of GitHub repositories to create webhooks for | <pre>list(object({<br>    name   = string<br>    events = list(string)<br>  }))</pre> | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| function\_arn | ARN of AWS Lambda function used to validate Github webhook request |
| invoke\_url | API invoke URL the github webhook will ping |

<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
