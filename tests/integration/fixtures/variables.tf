variable "testing_github_token" {
  description = <<EOF
GitHub token to create GitHub webhook for repos defined in var.repos (permission: )
The permissions for the token is dependent on if the repos has public or private visibility.
Permissions:
  private:
    - admin:repo_hook
    - repo
    - read:org (if organization repo)
    - delete_repo
    - read:discussion
  public:
    - admin:repo_hook
    - repo:status
    - public_repo
    - read:org (if organization repo)
    - delete_repo
    - read:discussion
See more about OAuth scopes here: https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps
EOF
  type        = string
  sensitive   = true
  default     = null
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