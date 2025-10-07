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
      className="min-h-screen bg-cover bg-center bg-no-repeat flex items-center justify-center"
      style={{ backgroundImage: `url(${BRANDING.customer.background.login})` }}
    >
      <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-xl p-8 w-full max-w-md">
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
    </div>
  );
};

export default AuthAmplify;
