locals {
  preview_color = var.active_color == "blue" ? "green" : "blue"
  # Directories, not single files, are mounted so a rewritten file is visible inside the running container.
  generated_dir = abspath("${path.module}/../generated")
}

# One image serves both the fixed-response apps and the proxy.
resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_network" "lab" {
  name = "mo-bg-net"
}

resource "local_file" "app_conf" {
  for_each = var.releases

  filename = "${local.generated_dir}/${each.key}/default.conf"
  content = templatefile("${path.module}/templates/app.conf.tftpl", {
    color       = each.key
    version     = each.value.version
    ready       = each.value.ready
    quote_total = each.value.quote_total
  })
}

resource "local_file" "proxy_conf" {
  filename = "${local.generated_dir}/proxy/default.conf"
  content = templatefile("${path.module}/templates/proxy.conf.tftpl", {
    live_color    = var.active_color
    preview_color = local.preview_color
  })
}

resource "docker_container" "app" {
  for_each = var.releases

  name  = "mo-bg-${each.key}"
  image = docker_image.nginx.image_id

  networks_advanced {
    name = docker_network.lab.id
  }

  volumes {
    host_path      = dirname(local_file.app_conf[each.key].filename)
    container_path = "/etc/nginx/conf.d"
    read_only      = true
  }

  lifecycle {
    # A release change is a new container; nginx would otherwise keep serving the old config.
    replace_triggered_by = [local_file.app_conf[each.key]]
  }
}

resource "docker_container" "proxy" {
  name  = "mo-bg-proxy"
  image = docker_image.nginx.image_id

  networks_advanced {
    name = docker_network.lab.id
  }

  # Only the proxy publishes ports, and only on loopback.
  ports {
    internal = 8080
    external = 8080
    ip       = "127.0.0.1"
  }

  ports {
    internal = 8081
    external = 8081
    ip       = "127.0.0.1"
  }

  volumes {
    host_path      = dirname(local_file.proxy_conf.filename)
    container_path = "/etc/nginx/conf.d"
    read_only      = true
  }

  # Routing changes are not replacements: Terraform writes the file, scripts/reload_proxy.py activates it.
  depends_on = [docker_container.app]
}
