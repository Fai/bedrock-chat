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
    <Authenticator
      socialProviders={socialProviders}
      components={{
        Header: () => (
          <div className="mb-5 mt-10 flex justify-center">
            <CustomerLogo variant="full" />
          </div>
        ),
        SignIn: {
          Header: () => (
            <div className="mb-5 mt-10 flex justify-center">
              <CustomerLogo variant="full" />
            </div>
          ),
          Footer: () => <div></div>
        },
        SignUp: {
          Header: () => (
            <div className="mb-5 mt-10 flex justify-center">
              <CustomerLogo variant="full" />
            </div>
          ),
          Footer: () => <div></div>
        }
      }}
      style={{
        '--amplify-components-authenticator-router-background': `url(${BRANDING.customer.background.login})`,
        '--amplify-components-authenticator-router-background-size': 'cover',
        '--amplify-components-authenticator-router-background-position': 'center',
        '--amplify-components-authenticator-router-background-repeat': 'no-repeat'
      } as React.CSSProperties}>
      <>{cloneElement(children as ReactElement, { signOut })}</>
    </Authenticator>
  );
};

export default AuthAmplify;
