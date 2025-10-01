"use client";

import { useState } from "react";
import SparkMD5 from "spark-md5";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, CheckCircle, FileText, Loader2 } from "lucide-react";
import {
  createProfileResumeUploadUrlApiV1ProfileProfileResumeUploadPost,
  startProfileResumeExtractionApiV1ProfileProfileResumeExtractResumeIdPost,
} from "@/lib/api/generated/api";

export default function ResumeUploadTestPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadCompleted, setUploadCompleted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculateChecksums = async (
    file: File
  ): Promise<{ sha256: string; md5: string }> => {
    const arrayBuffer = await file.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);

    // Calculate SHA-256
    const sha256Buffer = await crypto.subtle.digest("SHA-256", uint8Array);
    const sha256Array = Array.from(new Uint8Array(sha256Buffer));
    const sha256 = sha256Array
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");

    // Calculate MD5 using SparkMD5 since the Web Crypto API does not expose MD5
    const md5 = await calculateMD5(uint8Array);

    return { sha256, md5 };
  };

  const calculateMD5 = async (data: Uint8Array): Promise<string> => {
    const normalized =
      data.byteOffset === 0 && data.byteLength === data.buffer.byteLength
        ? data
        : data.slice();

    return SparkMD5.ArrayBuffer.hash(normalized.buffer as ArrayBuffer);
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

      // Get signed upload URL
      const uploadUrlResponse =
        await createProfileResumeUploadUrlApiV1ProfileProfileResumeUploadPost({
          sha256_checksum: sha256,
          md5_checksum: md5,
          content_type: "application/pdf",
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
        throw new Error("Failed to upload file to signed URL");
      }

      setUploadCompleted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      console.error("Upload error:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!fileId) return;

    setAnalyzing(true);
    setError(null);

    try {
      const response =
        await startProfileResumeExtractionApiV1ProfileProfileResumeExtractResumeIdPost(
          "placeholder-resume-id", // This should come from somewhere
          { file_id: fileId }
        );

      console.log("Analysis started:", response);
      alert(`Analysis started successfully! File ID: ${response.file_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
      console.error("Analysis error:", err);
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
