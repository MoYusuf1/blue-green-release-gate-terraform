variable "active_color" {
  description = "Release that receives live traffic on port 8080. The other is served on preview port 8081."
  type        = string

  validation {
    condition     = contains(["blue", "green"], var.active_color)
    error_message = "active_color must be blue or green."
  }
}

variable "releases" {
  description = "Per-color release settings. quote_total is what the app returns, not what the release check expects."
  type = map(object({
    version     = string
    ready       = bool
    quote_total = number
  }))

  validation {
    condition     = toset(keys(var.releases)) == toset(["blue", "green"])
    error_message = "releases must define exactly blue and green."
  }
}
