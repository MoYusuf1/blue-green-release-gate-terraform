# Plan-only tests with a mocked Docker provider: no daemon, no containers, no cost.

mock_provider "docker" {}

variables {
  active_color = "blue"
  releases = {
    blue  = { version = "v1", ready = true, quote_total = 1200 }
    green = { version = "v2", ready = true, quote_total = 1200 }
  }
}

run "live_goes_to_active_color_and_preview_to_the_other" {
  command = plan

  assert {
    condition     = can(regex("listen 8080;[^}]*mo-bg-blue:80", local_file.proxy_conf.content))
    error_message = "Live port 8080 must route to the active release (blue)."
  }
  assert {
    condition     = can(regex("listen 8081;[^}]*mo-bg-green:80", local_file.proxy_conf.content))
    error_message = "Preview port 8081 must route to the other release (green)."
  }
}

run "promoting_green_swaps_live_and_preview" {
  command = plan
  variables {
    active_color = "green"
  }

  assert {
    condition     = can(regex("listen 8080;[^}]*mo-bg-green:80", local_file.proxy_conf.content)) && can(regex("listen 8081;[^}]*mo-bg-blue:80", local_file.proxy_conf.content))
    error_message = "Promoting green must send live traffic to green and preview to blue."
  }
}

run "each_release_serves_its_own_quote_and_readiness" {
  command = plan
  variables {
    releases = {
      blue  = { version = "v1", ready = true, quote_total = 1200 }
      green = { version = "v2-bad", ready = false, quote_total = 999 }
    }
  }

  assert {
    condition     = strcontains(local_file.app_conf["green"].content, "\"total_cents\":999") && strcontains(local_file.app_conf["green"].content, "return 503")
    error_message = "Green must serve its configured quote and report not ready."
  }
  assert {
    condition     = strcontains(local_file.app_conf["blue"].content, "\"total_cents\":1200") && strcontains(local_file.app_conf["blue"].content, "return 200")
    error_message = "A change to green must not change blue."
  }
}

run "only_the_proxy_publishes_ports_and_only_on_loopback" {
  command = plan

  assert {
    condition     = length(docker_container.proxy.ports) == 2 && alltrue([for p in docker_container.proxy.ports : p.ip == "127.0.0.1"])
    error_message = "The proxy must publish exactly two ports, both on 127.0.0.1."
  }
  assert {
    condition     = alltrue([for c in docker_container.app : length(c.ports) == 0])
    error_message = "Application containers must not publish ports."
  }
}

run "rejects_an_unknown_live_color" {
  command = plan
  variables {
    active_color = "purple"
  }
  expect_failures = [var.active_color]
}

run "rejects_a_missing_release" {
  command = plan
  variables {
    releases = {
      blue = { version = "v1", ready = true, quote_total = 1200 }
    }
  }
  expect_failures = [var.releases]
}
