resource "aws_s3_bucket" "backend_storage" {
  bucket = "resume-genius-backend-storage"
}

resource "aws_s3_bucket_cors_configuration" "backend_storage" {
  bucket = aws_s3_bucket.backend_storage.id

  cors_rule {
    allowed_methods = ["GET", "PUT", "HEAD"]
    allowed_origins = [
      "http://localhost:3000",
      "https://localhost:3000",
      "http://127.0.0.1:3000",
      "https://127.0.0.1:3000",
    ]
    allowed_headers = ["*"]
    expose_headers = ["ETag", "x-amz-request-id"]
    max_age_seconds = 3000
  }
}
