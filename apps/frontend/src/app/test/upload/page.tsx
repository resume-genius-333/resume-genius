"use client";

import { useState } from "react";
import SparkMD5 from "spark-md5";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, CheckCircle, FileText, Loader2 } from "lucide-react";
import {
  createProfileResumeUploadUrlApiV1ProfileProfileResumeUploadPost,
  startProfileResumeExtractionApiV1ProfileProfileResumeExtractFileIdPost,
} from "@/lib/api/generated/api";

export default function ResumeUploadTestPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadCompleted, setUploadCompleted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const logErrorDetails = (context: string, err: unknown) => {
    if (err && typeof err === "object" && "response" in err) {
      const response = (
        err as {
          message?: string;
          response?: { status?: number; statusText?: string; data?: unknown };
        }
      ).response;
      console.error(context, {
        message: (err as { message?: string }).message,
        status: response?.status,
        statusText: response?.statusText,
        data: response?.data,
      });
      return;
    }

    console.error(context, err);
  };

  const bytesToBase64 = (bytes: Uint8Array): string => {
    const chunkSize = 0x8000;
    let binary = "";
    for (let i = 0; i < bytes.length; i += chunkSize) {
      const chunk = bytes.subarray(i, i + chunkSize);
      binary += String.fromCharCode(...chunk);
    }
    return btoa(binary);
  };

  const calculateChecksums = async (
    file: File
  ): Promise<{ sha256: string; md5: string }> => {
    const arrayBuffer = await file.arrayBuffer();

    // Calculate SHA-256 as base64
    const sha256Buffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
    const sha256 = bytesToBase64(new Uint8Array(sha256Buffer));

    // Calculate MD5 as base64 using SparkMD5 (Web Crypto API lacks MD5)
    const md5Hasher = new SparkMD5.ArrayBuffer();
    md5Hasher.append(arrayBuffer);
    const md5Binary = md5Hasher.end(true); // raw binary output
    const md5 = btoa(md5Binary);

    return { sha256, md5 };
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadCompleted(false);
      setFileId(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);

    try {
      // Calculate checksums
      const { sha256, md5 } = await calculateChecksums(selectedFile);
      const contentType = selectedFile.type || "application/octet-stream";

      // Get signed upload URL
      const uploadUrlResponse =
        await createProfileResumeUploadUrlApiV1ProfileProfileResumeUploadPost({
          sha256_checksum: sha256,
          md5_checksum: md5,
          content_type: contentType,
        });

      console.log(uploadUrlResponse);

      const {
        file_id: newFileId,
        upload_url: uploadUrl,
        required_headers: requiredHeaders,
      } = uploadUrlResponse;
      setFileId(newFileId);

      // Upload file to signed URL
      const uploadResponse = await fetch(uploadUrl, {
        method: "PUT",
        body: selectedFile,
        headers: {
          ...requiredHeaders,
        },
      });

      if (!uploadResponse.ok) {
        const errorText = await uploadResponse.text();
        console.error("Upload to S3 failed", {
          status: uploadResponse.status,
          statusText: uploadResponse.statusText,
          body: errorText,
        });
        throw new Error(
          `Upload failed (${uploadResponse.status} ${uploadResponse.statusText})`
        );
      }

      setUploadCompleted(true);
    } catch (err) {
      logErrorDetails("Upload error", err);
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!fileId) return;

    setAnalyzing(true);
    setError(null);

    try {
      const url =
        await startProfileResumeExtractionApiV1ProfileProfileResumeExtractFileIdPost(
          fileId
        );

      console.log("Analysis started:", url);
      alert(`Analysis started successfully! ${url}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      logErrorDetails("Analysis error", err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Resume Upload Test
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* File Selection */}
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-8 hover:border-primary transition-colors">
              <Upload className="h-12 w-12 text-gray-400 mb-4" />
              <label
                htmlFor="file-upload"
                className="cursor-pointer text-sm text-primary hover:underline"
              >
                Choose a file
              </label>
              <input
                id="file-upload"
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx"
                onChange={handleFileSelect}
              />
              {selectedFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>

            {/* Upload Button */}
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || uploading || uploadCompleted}
              className="w-full"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Uploading...
                </>
              ) : uploadCompleted ? (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Upload Completed
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload File
                </>
              )}
            </Button>
          </div>

          {/* Success Indicator */}
          {uploadCompleted && (
            <div className="flex items-center justify-center p-4 bg-green-50 rounded-lg">
              <CheckCircle className="h-8 w-8 text-green-500" />
              <span className="ml-2 text-green-700 font-medium">
                File uploaded successfully!
              </span>
            </div>
          )}

          {/* Start Analysis Button */}
          {uploadCompleted && (
            <Button
              onClick={handleStartAnalysis}
              disabled={analyzing}
              variant="outline"
              className="w-full"
            >
              {analyzing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                "Start Analysis"
              )}
            </Button>
          )}

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Debug Info */}
          {fileId && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-600">File ID: {fileId}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
