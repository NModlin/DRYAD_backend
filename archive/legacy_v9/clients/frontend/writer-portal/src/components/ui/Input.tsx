'use client';

import React from 'react';
import { cn } from '@/utils/helpers';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onRightIconClick?: () => void;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    type = 'text',
    label,
    error,
    helperText,
    leftIcon,
    rightIcon,
    onRightIconClick,
    disabled,
    ...props 
  }, ref) => {
    const hasError = !!error;
    
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span className="text-gray-400 sm:text-sm">{leftIcon}</span>
            </div>
          )}
          
          <input
            type={type}
            className={cn(
              'block w-full rounded-md border-gray-300 shadow-sm transition-colors',
              'focus:border-primary-500 focus:ring-primary-500',
              'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              hasError && 'border-error-300 focus:border-error-500 focus:ring-error-500',
              className
            )}
            ref={ref}
            disabled={disabled}
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
              {onRightIconClick ? (
                <button
                  type="button"
                  onClick={onRightIconClick}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none"
                  disabled={disabled}
                >
                  {rightIcon}
                </button>
              ) : (
                <span className="text-gray-400 sm:text-sm">{rightIcon}</span>
              )}
            </div>
          )}
        </div>
        
        {(error || helperText) && (
          <div className="mt-1">
            {error && (
              <p className="text-sm text-error-600">{error}</p>
            )}
            {!error && helperText && (
              <p className="text-sm text-gray-500">{helperText}</p>
            )}
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
export default Input;
