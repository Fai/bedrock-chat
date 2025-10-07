import React, {
  ReactNode,
  useState,
  useEffect,
  cloneElement,
  ReactElement,
} from 'react';
import Button from './Button';
import { BaseProps } from '../@types/common';
import { getCurrentUser, signInWithRedirect, signOut } from 'aws-amplify/auth';
import { useTranslation } from 'react-i18next';
import { PiCircleNotch } from 'react-icons/pi';
import CustomerLogo from './CustomerLogo';
import { BRANDING } from '../constants/branding';

type Props = BaseProps & {
  children: ReactNode;
};

const AuthCustom: React.FC<Props> = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    getCurrentUser()
      .then(() => {
        setAuthenticated(true);
      })
      .catch(() => {
        setAuthenticated(false);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleSignIn = () => {
    signInWithRedirect({
      provider: {
        custom: import.meta.env.VITE_APP_CUSTOM_PROVIDER_NAME,
      },
    });
  };

  const handleSignOut = () => {
    signOut();
  };

  return (
    <>
      {loading ? (
        <div 
          className="min-h-screen bg-cover bg-center bg-no-repeat flex items-center justify-center"
          style={{ backgroundImage: `url(${BRANDING.customer.background.login})` }}
        >
          <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-xl p-8 flex justify-center">
            <div className="flex flex-col items-center p-4">
              <div className="mb-3 text-4xl">Loading...</div>
              <div className="animate-spin">
                <PiCircleNotch size={100} />
              </div>
            </div>
          </div>
        </div>
      ) : !authenticated ? (
        <div 
          className="min-h-screen bg-cover bg-center bg-no-repeat flex items-center justify-center"
          style={{ backgroundImage: `url(${BRANDING.customer.background.login})` }}
        >
          <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-xl p-8">
            <div className="flex flex-col items-center gap-4">
              <div className="mb-5 mt-10">
                <CustomerLogo variant="full" />
              </div>
              <Button onClick={() => handleSignIn()} className="px-20 text-xl">
                {t('signIn.button.login')}
              </Button>
            </div>
          </div>
        </div>
      ) : (
        // No background for authenticated state - just pass through to app
        <>
          {cloneElement(children as ReactElement, { signOut: handleSignOut })}
        </>
      )}
    </>
  );
};

export default AuthCustom;
