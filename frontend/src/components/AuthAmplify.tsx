import React, { ReactNode, cloneElement, ReactElement } from 'react';
import { BaseProps } from '../@types/common';
import { Authenticator } from '@aws-amplify/ui-react';
import { useAuthenticator } from '@aws-amplify/ui-react';
import { SocialProvider } from '../@types/auth';
import CustomerLogo from './CustomerLogo';
import { BRANDING } from '../constants/branding';

type Props = BaseProps & {
  socialProviders: SocialProvider[];
  children: ReactNode;
};

const AuthAmplify: React.FC<Props> = ({ socialProviders, children }) => {
  const { signOut } = useAuthenticator();

  return (
    <div 
      className="min-h-screen bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: `url(${BRANDING.customer.background.login})` }}
    >
      <Authenticator
        socialProviders={socialProviders}
        components={{
          Header: () => (
            <div className="mb-5 mt-10 flex justify-center">
              <CustomerLogo variant="full" />
            </div>
          ),
        }}>
        <>{cloneElement(children as ReactElement, { signOut })}</>
      </Authenticator>
    </div>
  );
};

export default AuthAmplify;
