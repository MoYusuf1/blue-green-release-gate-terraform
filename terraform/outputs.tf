output "configured_live_color" {
  description = "What Terraform configured. Not proof of what NGINX is serving until the proxy is reloaded."
  value       = var.active_color
}

output "live_url" {
  description = "Live traffic, routed to the active release."
  value       = "http://127.0.0.1:8080"
}

output "preview_url" {
  description = "Preview of the release that is not live, for checking a candidate."
  value       = "http://127.0.0.1:8081"
}
