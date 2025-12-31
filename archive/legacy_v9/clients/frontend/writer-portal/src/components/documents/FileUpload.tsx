'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { cn, formatFileSize, getFileTypeIcon } from '@/utils/helpers';
import { FILE_UPLOAD } from '@/utils/constants';
import { Button } from '@/components/ui/Button';

interface FileUploadProps {
  onUpload: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number;
  acceptedTypes?: string[];
  disabled?: boolean;
  className?: string;
}

interface FileWithProgress extends File {
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

export function FileUpload({
  onUpload,
  maxFiles = FILE_UPLOAD.MAX_FILES_PER_BATCH,
  maxSize = FILE_UPLOAD.MAX_FILE_SIZE,
  acceptedTypes = FILE_UPLOAD.ALLOWED_TYPES,
  disabled = false,
  className
}: FileUploadProps) {
  const [files, setFiles] = useState<FileWithProgress[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errors = rejectedFiles.map(({ file, errors }) => ({
        file: file.name,
        errors: errors.map((e: any) => e.message).join(', ')
      }));
      console.error('File upload errors:', errors);
    }

    // Process accepted files
    const newFiles: FileWithProgress[] = acceptedFiles.map(file => ({
      ...file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      progress: 0,
      status: 'pending' as const
    }));

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive: dropzoneActive } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxFiles,
    maxSize,
    disabled,
    multiple: maxFiles > 1
  });

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const startUpload = () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    if (pendingFiles.length > 0) {
      onUpload(pendingFiles);
      
      // Simulate upload progress (replace with actual upload logic)
      pendingFiles.forEach(file => {
        setFiles(prev => prev.map(f => 
          f.id === file.id ? { ...f, status: 'uploading' } : f
        ));
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.random() * 20;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setFiles(prev => prev.map(f => 
              f.id === file.id ? { ...f, progress: 100, status: 'completed' } : f
            ));
          } else {
            setFiles(prev => prev.map(f => 
              f.id === file.id ? { ...f, progress } : f
            ));
          }
        }, 200);
      });
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'completed'));
  };

  const clearAll = () => {
    setFiles([]);
  };

  const pendingCount = files.filter(f => f.status === 'pending').length;
  const uploadingCount = files.filter(f => f.status === 'uploading').length;
  const completedCount = files.filter(f => f.status === 'completed').length;

  return (
    <div className={cn('w-full', className)}>
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive || dropzoneActive
            ? 'border-primary-400 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          <div className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center',
            isDragActive || dropzoneActive
              ? 'bg-primary-100 text-primary-600'
              : 'bg-gray-100 text-gray-400'
          )}>
            <Upload className="w-6 h-6" />
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop files here' : 'Upload your documents'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop files here, or click to browse
            </p>
          </div>
          
          <div className="text-xs text-gray-400 space-y-1">
            <p>Supported formats: PDF, DOC, DOCX, TXT, MD, CSV, XLS, XLSX, Images</p>
            <p>Maximum file size: {formatFileSize(maxSize)}</p>
            <p>Maximum files: {maxFiles}</p>
          </div>
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Files ({files.length})
            </h3>
            <div className="flex space-x-2">
              {completedCount > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearCompleted}
                >
                  Clear Completed
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={clearAll}
              >
                Clear All
              </Button>
              {pendingCount > 0 && (
                <Button
                  onClick={startUpload}
                  disabled={uploadingCount > 0}
                  loading={uploadingCount > 0}
                >
                  Upload {pendingCount} File{pendingCount !== 1 ? 's' : ''}
                </Button>
              )}
            </div>
          </div>

          <div className="space-y-2">
            {files.map((file) => (
              <FileItem
                key={file.id}
                file={file}
                onRemove={() => removeFile(file.id)}
              />
            ))}
          </div>

          {/* Upload summary */}
          {(uploadingCount > 0 || completedCount > 0) && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between text-sm">
                <div className="space-x-4">
                  {uploadingCount > 0 && (
                    <span className="text-blue-600">
                      {uploadingCount} uploading...
                    </span>
                  )}
                  {completedCount > 0 && (
                    <span className="text-green-600">
                      {completedCount} completed
                    </span>
                  )}
                </div>
                <div className="text-gray-500">
                  {files.length} total
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Individual file item component
interface FileItemProps {
  file: FileWithProgress;
  onRemove: () => void;
}

function FileItem({ file, onRemove }: FileItemProps) {
  const getStatusIcon = () => {
    switch (file.status) {
      case 'pending':
        return <File className="w-5 h-5 text-gray-400" />;
      case 'uploading':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <File className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (file.status) {
      case 'pending':
        return 'border-gray-200';
      case 'uploading':
        return 'border-blue-200 bg-blue-50';
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200';
    }
  };

  return (
    <div className={cn(
      'flex items-center p-3 border rounded-lg',
      getStatusColor()
    )}>
      <div className="flex-shrink-0 mr-3">
        {getStatusIcon()}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {file.name}
            </p>
            <p className="text-xs text-gray-500">
              {formatFileSize(file.size)}
              {file.status === 'error' && file.error && (
                <span className="text-red-500 ml-2">• {file.error}</span>
              )}
            </p>
          </div>
          
          {file.status !== 'uploading' && (
            <button
              onClick={onRemove}
              className="ml-2 p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        {file.status === 'uploading' && (
          <div className="mt-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${file.progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {Math.round(file.progress)}% uploaded
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
