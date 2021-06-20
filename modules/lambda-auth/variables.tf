# AGW #
variable "api_name" {
  description = "Name of API-Gateway"
  type        = string
  default     = null
}

variable "api_description" {
  description = "Description for API-Gateway"
  type        = string
  default     = "API used for custom GitHub webhooks"
}



variable "repos" {
  description = <<EOF
List of named repos to create github webhooks for and their respective filter groups
Params:
  `name`: Repository name
  `filter_groups`: {
    `events` - List of Github Webhook events that will invoke the API. Currently only supports: `push` and `pull_request`.
    `pr_actions` - List of pull request actions (e.g. opened, edited, reopened, closed). See more under the action key at: https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request
    `base_refs` - List of base refs
    `head_refs` - List of head refs
    `actor_account_ids` - List of Github user IDs
    `commit_messages` - List of commit messages
    `file_paths` - List of file paths
    `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched
  }
  EOF
  type = list(object({
    name = string
    filter_groups = optional(list(object({
      events                 = list(string)
      pr_actions             = optional(list(string))
      base_refs              = optional(list(string))
      head_refs              = optional(list(string))
      actor_account_ids      = optional(list(string))
      commit_messages        = optional(list(string))
      file_paths             = optional(list(string))
      exclude_matched_filter = optional(bool)
    })))
  }))
  default = []
}

# SSM #

## github-token ##

variable "github_token_ssm_description" {
  description = "Github token SSM parameter description"
  type        = string
  default     = "Github token used to give read access to the payload validator function to get file that differ between commits" #tfsec:ignore:GEN001
}

variable "github_token_ssm_key" {
  description = "AWS SSM Parameter Store key for sensitive Github personal token"
  type        = string
  default     = "github-webhook-validator-token" #tfsec:ignore:GEN001
}

variable "github_token_ssm_value" {
  description = "Registered Github webhook token associated with the Github provider. If not provided, module looks for pre-existing SSM parameter via `github_token_ssm_key`"
  type        = string
  default     = ""
  sensitive   = true
}

variable "create_github_token_ssm_param" {
  description = "Determines if an AWS System Manager Parameter Store value should be created for the Github token"
  type        = bool
  default     = true
}

variable "github_token_ssm_tags" {
  description = "Tags for Github token SSM parameter"
  type        = map(string)
  default     = {}
}

## github-secret ##

variable "github_secret_ssm_key" {
  description = "Key for github secret within AWS SSM Parameter Store"
  type        = string
  default     = "github-webhook-github-secret" #tfsec:ignore:GEN001
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

variable "lambda_success_destination_arns" {
  description = "AWS ARNs of services that will be invoked if Lambda function succeeds"
  type        = list(string)
  default     = []
}

variable "lambda_failure_destination_arns" {
  description = "AWS ARNs of services that will be invoked if Lambda function fails"
  type        = list(string)
  default     = []
}

variable "function_name" {
  description = "Name of Lambda function"
  type        = string
  default     = "github-webhook-request-validator"
}