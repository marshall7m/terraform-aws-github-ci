<!-- BEGINNING OF PRE-COMMIT-TERRAFORM DOCS HOOK -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >=0.15.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 3.22 |
| <a name="requirement_github"></a> [github](#requirement\_github) | >=4.4.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 3.22 |
| <a name="provider_github"></a> [github](#provider\_github) | >=4.4.0 |
| <a name="provider_local"></a> [local](#provider\_local) | n/a |
| <a name="provider_random"></a> [random](#provider\_random) | n/a |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_lambda_function"></a> [lambda\_function](#module\_lambda\_function) | terraform-aws-modules/lambda/aws | 3.3.1 |

## Resources

| Name | Type |
|------|------|
| [aws_api_gateway_deployment.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment) | resource |
| [aws_api_gateway_integration.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration) | resource |
| [aws_api_gateway_integration_response.status_200](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration_response) | resource |
| [aws_api_gateway_integration_response.status_400](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration_response) | resource |
| [aws_api_gateway_integration_response.status_500](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_integration_response) | resource |
| [aws_api_gateway_method.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method) | resource |
| [aws_api_gateway_method_response.status_200](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method_response) | resource |
| [aws_api_gateway_method_response.status_400](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method_response) | resource |
| [aws_api_gateway_method_response.status_500](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method_response) | resource |
| [aws_api_gateway_method_settings.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_method_settings) | resource |
| [aws_api_gateway_model.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_model) | resource |
| [aws_api_gateway_resource.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_resource) | resource |
| [aws_api_gateway_rest_api.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api) | resource |
| [aws_api_gateway_stage.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_stage) | resource |
| [aws_cloudwatch_log_group.agw](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_iam_policy.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_ssm_parameter.github_secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.github_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [github_repository_webhook.this](https://registry.terraform.io/providers/integrations/github/latest/docs/resources/repository_webhook) | resource |
| [local_file.filter_groups](https://registry.terraform.io/providers/hashicorp/local/latest/docs/resources/file) | resource |
| [random_password.github_webhook_secret](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) | resource |
| [aws_iam_policy_document.lambda](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_kms_key.ssm](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/kms_key) | data source |
| [aws_ssm_parameter.github_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_api_description"></a> [api\_description](#input\_api\_description) | Description for API-Gateway | `string` | `"API used for custom GitHub webhooks"` | no |
| <a name="input_api_id"></a> [api\_id](#input\_api\_id) | Pre-existing AWS API ID to attach resources to. If not specified, a new API will be created and defining var.api\_name will be required | `string` | `null` | no |
| <a name="input_api_name"></a> [api\_name](#input\_api\_name) | Name of API-Gateway to be created | `string` | `"github-webhook"` | no |
| <a name="input_api_resource_path"></a> [api\_resource\_path](#input\_api\_resource\_path) | AWS API resource path part to create | `string` | `"github"` | no |
| <a name="input_async_lambda_invocation"></a> [async\_lambda\_invocation](#input\_async\_lambda\_invocation) | Determines if the backend Lambda function for the API Gateway is invoked asynchronously.<br>If true, the API Gateway REST API method will not return the Lambda results to the client.<br>See for more info: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html | `bool` | `false` | no |
| <a name="input_create_api"></a> [create\_api](#input\_create\_api) | Determines if Terraform module just create the AWS REST API | `bool` | n/a | yes |
| <a name="input_deployment_triggers"></a> [deployment\_triggers](#input\_deployment\_triggers) | Arbitrary mapping that when changed causes a redeployment of the API | `map(string)` | `{}` | no |
| <a name="input_enable_api_cw_logs"></a> [enable\_api\_cw\_logs](#input\_enable\_api\_cw\_logs) | Determines API execution logs should be stored within a Cloudwatch log group | `bool` | `true` | no |
| <a name="input_execution_arn"></a> [execution\_arn](#input\_execution\_arn) | Pre-existing AWS API execution ARN that will be allowed to invoke the Lambda function | `string` | `null` | no |
| <a name="input_function_name"></a> [function\_name](#input\_function\_name) | Name of Lambda function | `string` | `"github-webhook-request-validator"` | no |
| <a name="input_github_secret_ssm_description"></a> [github\_secret\_ssm\_description](#input\_github\_secret\_ssm\_description) | Github secret SSM parameter description | `string` | `"Secret value for Github Webhooks"` | no |
| <a name="input_github_secret_ssm_key"></a> [github\_secret\_ssm\_key](#input\_github\_secret\_ssm\_key) | Key for github secret within AWS SSM Parameter Store | `string` | `null` | no |
| <a name="input_github_secret_ssm_tags"></a> [github\_secret\_ssm\_tags](#input\_github\_secret\_ssm\_tags) | Tags for Github webhook secret SSM parameter | `map(string)` | `{}` | no |
| <a name="input_lambda_attach_async_event_policy"></a> [lambda\_attach\_async\_event\_policy](#input\_lambda\_attach\_async\_event\_policy) | Determines if a policy should be attached to the Lambda Function's role to allow asynchronous calls to destination ARNs | `bool` | `false` | no |
| <a name="input_lambda_destination_on_failure"></a> [lambda\_destination\_on\_failure](#input\_lambda\_destination\_on\_failure) | AWS ARN of the service that will be invoked if Lambda function fails | `string` | `null` | no |
| <a name="input_lambda_destination_on_success"></a> [lambda\_destination\_on\_success](#input\_lambda\_destination\_on\_success) | AWS ARN of the service that will be invoked if Lambda function succeeds | `string` | `null` | no |
| <a name="input_lambda_vpc_attach_network_policy"></a> [lambda\_vpc\_attach\_network\_policy](#input\_lambda\_vpc\_attach\_network\_policy) | Determines if VPC policy should be added to the Lambda Function's IAM role | `bool` | `false` | no |
| <a name="input_lambda_vpc_security_group_ids"></a> [lambda\_vpc\_security\_group\_ids](#input\_lambda\_vpc\_security\_group\_ids) | IDs of the AWS VPC security groups the Lambda Function will be attached to | `list(string)` | `[]` | no |
| <a name="input_lambda_vpc_subnet_ids"></a> [lambda\_vpc\_subnet\_ids](#input\_lambda\_vpc\_subnet\_ids) | IDs of the AWS VPC subnets the Lambda Function will be hosted in | `list(string)` | `[]` | no |
| <a name="input_repos"></a> [repos](#input\_repos) | List of named GitHub repos and their respective webhook, token and filter group(s) configurations.<br>The `github_token_ssm_key` and `github_token_ssm_value` only need to be defined if the repository is private.<br>The token defined under `github_token_ssm_value` needs the full `repo` permissions until github creates a repo scoped token with <br>granular permissions. See thread here: https://github.community/t/can-i-give-read-only-access-to-a-private-repo-from-a-developer-account/441/165<br>Params:<br>  `name`: Repository name<br>  `is_private`: Whether the repo's visibility is set to private<br>  `create_github_token_ssm_param`: Determines if the module should create or load the GitHub token AWS SSM parameter (defaults to true)<br>  `github_token_ssm_param_arn`: GitHub token AWS SSM Parameter Store ARN<br>  `github_token_ssm_key`: Key for the AWS SSM Parameter Store GitHub token resource<br>    If not defined, the module will generate one.<br>  `github_token_ssm_value`: Value for the AWS SSM Parameter Store GitHub token resource used for accessing the repo<br>  `github_token_ssm_tags`: Tags for the AWS SSM Parameter Store GitHub token resource<br>  `filter_groups`: List of filter groups that the Github event has to meet. The event has to meet all filters of atleast one group in order to succeed. <br>  [<br>    [ (Filter Group)<br>      {<br>        `type`: The type of filter<br>          (<br>            `event` - Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.<br>            `pr_action` - Pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request<br>            `base_ref` - Pull request base ref<br>            `head_ref` - Pull request head ref<br>            `actor_account_id` - Github user IDs<br>            `commit_message` - GitHub event's commit message<br>            `file_path` - File paths of new, modified, or deleted files<br>            `<JSONPATH>` - Valid JSON path expression that will be used to find the filter value(s) within the GitHub webhook payload<br>          )<br>        `pattern`: Regex pattern that is matched against the `type` payload attribute. For `type` = `event`, use a single Github webhook event and not a regex pattern.<br>        `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched<br>      }<br>    ]<br>  ] | <pre>list(object({<br>    name                          = string<br>    is_private                    = optional(bool)<br>    create_github_token_ssm_param = optional(bool)<br>    github_token_ssm_param_arn    = optional(string)<br>    github_token_ssm_key          = optional(string)<br>    github_token_ssm_value        = optional(string)<br>    github_token_ssm_tags         = optional(map(string))<br>    filter_groups = list(list(object({<br>      type                   = string<br>      pattern                = string<br>      exclude_matched_filter = optional(bool)<br>    })))<br>  }))</pre> | `[]` | no |
| <a name="input_root_resource_id"></a> [root\_resource\_id](#input\_root\_resource\_id) | Pre-existing AWS API resource ID associated with the API defined within var.api\_id to be used as the root resource ID for the github API resource | `string` | `null` | no |
| <a name="input_stage_name"></a> [stage\_name](#input\_stage\_name) | Stage name for the API deployment | `string` | `"prod"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_agw_log_group_arn"></a> [agw\_log\_group\_arn](#output\_agw\_log\_group\_arn) | ARN of the CloudWatch log group associated with the API gateway |
| <a name="output_agw_log_group_name"></a> [agw\_log\_group\_name](#output\_agw\_log\_group\_name) | Name of the CloudWatch log group associated with the API gateway |
| <a name="output_api_changes_sha"></a> [api\_changes\_sha](#output\_api\_changes\_sha) | SHA value of file that contains API-related configurations. Can be used as a trigger for API deployments (see AWS resource: aws\_api\_gateway\_deployment) |
| <a name="output_api_id"></a> [api\_id](#output\_api\_id) | SHA value of file that contains API-related configurations. Can be used as a trigger for API deployments (see AWS resource: aws\_api\_gateway\_deployment) |
| <a name="output_api_stage_name"></a> [api\_stage\_name](#output\_api\_stage\_name) | API stage name |
| <a name="output_deployment_invoke_url"></a> [deployment\_invoke\_url](#output\_deployment\_invoke\_url) | API stage's URL |
| <a name="output_function_arn"></a> [function\_arn](#output\_function\_arn) | ARN of AWS Lambda Function used to validate Github webhook request |
| <a name="output_function_name"></a> [function\_name](#output\_function\_name) | Name of the Lambda Function used to validate Github webhook request |
| <a name="output_github_token_ssm_arns"></a> [github\_token\_ssm\_arns](#output\_github\_token\_ssm\_arns) | ARNs of the GitHub token AWS SSM Parameter Store resources |
| <a name="output_github_webhook_invoke_url"></a> [github\_webhook\_invoke\_url](#output\_github\_webhook\_invoke\_url) | API URL the github webhook will ping |
| <a name="output_lambda_log_group_arn"></a> [lambda\_log\_group\_arn](#output\_lambda\_log\_group\_arn) | ARN of the CloudWatch log group associated with the Lambda Function |
| <a name="output_lambda_log_group_name"></a> [lambda\_log\_group\_name](#output\_lambda\_log\_group\_name) | Name of the CloudWatch log group associated with the Lambda Function |
| <a name="output_webhook_ids"></a> [webhook\_ids](#output\_webhook\_ids) | Map of repo webhook IDs |
| <a name="output_webhook_urls"></a> [webhook\_urls](#output\_webhook\_urls) | Map of repo webhook URLs |
<!-- END OF PRE-COMMIT-TERRAFORM DOCS HOOK -->

## Features

- Move Lambda webhook validator from Lambda integration to Lambda Authorizer once/if Lambda Authorizers can receive request `method.request.body`. This will open up the Lambda integration for user defined services. See issue: https://stackoverflow.com/questions/47400447/access-post-request-body-from-custom-authorizer-lambda-function

## Tests

## Requirements

- AWS account must have a pre-existing IAM role that allows AWS AGW to write logs to Cloudwatch log groups. See details here: https://aws.amazon.com/premiumsupport/knowledge-center/api-gateway-cloudwatch-logs/


# TODO