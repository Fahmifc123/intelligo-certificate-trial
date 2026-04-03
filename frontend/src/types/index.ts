// Form Data Types
export interface CertificateFormData {
  name: string;
  email: string;
  project_title: string;
  social_link: string;
}

// API Response Types
export interface CertificateResponse {
  status: 'success' | 'error';
  certificate_url?: string;
  message?: string;
  ocr_text?: string;
  ai_validation?: boolean;
}

// Component Props Types
export interface CertificateFormProps {
  formData: CertificateFormData;
  file: File | null;
  screenshot: File | null;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onScreenshotChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

export interface SuccessStateProps {
  certificateUrl: string;
  onReset: () => void;
}

export interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export interface Requirement {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
}
