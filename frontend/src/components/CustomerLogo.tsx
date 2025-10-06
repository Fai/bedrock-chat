import React from 'react';
import { twMerge } from 'tailwind-merge';
import { BRANDING } from '../constants/branding';

type Props = {
  variant?: 'full' | 'compact';
  className?: string;
};

const CustomerLogo: React.FC<Props> = ({ variant = 'full', className }) => {
  const baseClasses = variant === 'full' 
    ? 'h-16 w-auto max-w-xs' 
    : 'h-8 w-auto max-w-32';

  return (
    <img
      src={BRANDING.customer.logo.default}
      alt={BRANDING.customer.name}
      className={twMerge(baseClasses, 'object-contain', className)}
    />
  );
};

export default CustomerLogo;
