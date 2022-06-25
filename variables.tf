# AGW #
variable "create_api" {
  description = "Determines if Terraform module just create the AWS REST API"
  type        = bool
}

variable "api_id" {
  description = "Pre-existing AWS API ID to attach resources to. If not specified, a new API will be created and defining var.api_name will be required"
  type        = string
  default     = null
}

variable "api_resource_path" {
  description = "AWS API resource path part to create"
  type        = string
  default     = "github"
}

variable "root_resource_id" {
  description = "Pre-existing AWS API resource ID associated with the API defined within var.api_id to be used as the root resource ID for the github API resource"
  type        = string
  default     = null
}

variable "execution_arn" {
  description = "Pre-existing AWS API execution ARN that will be allowed to invoke the Lambda function"
  type        = string
  default     = null
}

variable "api_name" {
  description = "Name of API-Gateway to be created"
  type        = string
  default     = "github-webhook"
}

variable "api_description" {
  description = "Description for API-Gateway"
  type        = string
  default     = "API used for custom GitHub webhooks"
}

variable "enable_api_cw_logs" {
  description = "Determines API execution logs should be stored within a Cloudwatch log group"
  type        = bool
  default     = true
}

variable "stage_name" {
  description = "Stage name for the API deployment"
  type        = string
  default     = "prod"
}

variable "deployment_triggers" {
  description = "Arbitrary mapping that when changed causes a redeployment of the API"
  type        = map(string)
  default     = {}
}

variable "repos" {
  description = <<EOF
List of named GitHub repos and their respective webhook, token and filter group(s) configurations.
The `github_token_ssm_key` and `github_token_ssm_value` only need to be defined if the repository is private.
The token defined under `github_token_ssm_value` needs the full `repo` permissions until github creates a repo scoped token with 
granular permissions. See thread here: https://github.community/t/can-i-give-read-only-access-to-a-private-repo-from-a-developer-account/441/165
Params:
  `name`: Repository name
  `is_private`: Whether the repo's visibility is set to private
  `github_token_ssm_key`: Key for the AWS SSM Parameter Store GitHub token resource
    If not defined, the module will generate one.
  `github_token_ssm_value`: Value for the AWS SSM Parameter Store GitHub token resource used for accessing the repo
  `github_token_ssm_tags`: Tags for the AWS SSM Parameter Store GitHub token resource
  `filter_groups`: List of filter groups that the Github event has to meet. The event has to meet all filters of atleast one group in order to succeed. 
  [
    [ (Filter Group)
      {
        `type`: The type of filter
          (
            `event` - Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.
            `pr_action` - Pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request
            `base_ref` - Pull request base ref
            `head_ref` - Pull request head ref
            `actor_account_id` - Github user IDs
            `commit_message` - GitHub event's commit message
            `file_path` - File paths of new, modified, or deleted files
            `<JSONPATH>` - Valid JSON path expression that will be used to find the filter value(s) within the GitHub webhook payload
          )
        `pattern`: Regex pattern that is matched against the `type` payload attribute. For `type` = `event`, use a single Github webhook event and not a regex pattern.
        `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched
      }
    ]
  ]
  EOF
  type = list(object({
    name                   = string
    is_private             = optional(bool)
    github_token_ssm_key   = optional(string)
    github_token_ssm_value = optional(string)
    github_token_ssm_tags  = optional(map(string))
    filter_groups = list(list(object({
      type                   = string
      pattern                = string
      exclude_matched_filter = optional(bool)
    })))
  }))
  default = []
}

# SSM #

## GITHUB SECRET ##

variable "github_secret_ssm_key" {
  description = "Key for github secret within AWS SSM Parameter Store"
  type        = string
  default     = "github-webhook-secret" #tfsec:ignore:GEN001
}

variable "github_secret_ssm_description" {
  description = "Github secret SSM parameter description"
  type        = string
  default     = "Secret value for Github Webhooks" #tfsec:ignore:GEN001
}

variable "github_secret_ssm_tags" {
  description = "Tags for Github webhook secret SSM parameter"
  type        = map(string)
  default     = {}
}

# Lambda #

variable "async_lambda_invocation" {
  description = <<EOF
Determines if the backend Lambda function for the API Gateway is invoked asynchronously.
If true, the API Gateway REST API method will not return the Lambda results to the client.
See for more info: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-integration-async.html
  EOF
  type        = bool
  default     = false
}

variable "lambda_destination_on_success" {
  description = "AWS ARN of the service that will be invoked if Lambda function succeeds"
  type        = string
  default     = null
}

variable "lambda_destination_on_failure" {
  description = "AWS ARN of the service that will be invoked if Lambda function fails"
  type        = string
  default     = null
}

variable "lambda_vpc_subnet_ids" {
  description = "IDs of the AWS VPC subnets the Lambda Function will be hosted in"
  type        = list(string)
  default     = []
}

variable "lambda_vpc_security_group_ids" {
  description = "IDs of the AWS VPC security groups the Lambda Function will be attached to"
  type        = list(string)
  default     = []
}

variable "lambda_vpc_attach_network_policy" {
  description = "Determines if VPC policy should be added to the Lambda Function's IAM role"
  type        = bool
  default     = false
}

variable "function_name" {
  description = "Name of Lambda function"
  type        = string
  default     = "github-webhook-request-validator"
}