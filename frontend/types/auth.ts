export type AuthTab = "login" | "register";

export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm extends LoginForm {
  passwordConfirm: string;
}

export interface SignupResponse {
  user: {
    id: string;
    email: string;
    remind_days_before: number;
    plan_status: "free" | "pro";
    monthly_scan_count: number;
  };
  personal_group: {
    id: string;
    name: string;
  };
}