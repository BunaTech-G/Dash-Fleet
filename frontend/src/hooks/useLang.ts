import { useOutletContext } from 'react-router-dom';
import type { Lang } from '../i18n';

export function useLang(): Lang {
  const ctx = useOutletContext<{ lang: Lang }>();
  return ctx?.lang || 'fr';
}
