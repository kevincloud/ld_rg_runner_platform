resource "null_resource" "python_ldsdk" {
  triggers = {
    build_number = timestamp()
  }

  provisioner "local-exec" {
    command = "pip install --target ${path.module}/app/ --upgrade launchdarkly-server-sdk"
  }
}

resource "null_resource" "python_names" {
  triggers = {
    build_number = timestamp()
  }

  provisioner "local-exec" {
    command = "pip install --target ${path.module}/app/ --upgrade names"
  }
}

resource "null_resource" "python_requests" {
  triggers = {
    build_number = timestamp()
  }

  provisioner "local-exec" {
    command = "pip install --target ${path.module}/app/ --upgrade requests"
  }
}
