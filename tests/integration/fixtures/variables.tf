variable "repos" {
  description = <<EOF
List of named repos to create github webhooks for and their respective filter groups
Params:
  `name`: Repository name
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
          )
        `pattern`: Regex pattern that is searched for within the related event's payload attributes. For `type` = `event`, use a single Github webhook event and not a regex pattern.
        `exclude_matched_filter` - If set to true, labels filter group as invalid if it is matched
      }
    ]
  ]
  EOF
  type = list(object({
    name = string
    filter_groups = list(list(object({
      type                   = string
      pattern                = string
      exclude_matched_filter = optional(bool)
    })))
  }))
  default = []
}