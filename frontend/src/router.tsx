import { createBrowserRouter } from 'react-router-dom';
import { LivePage } from './pages/LivePage';
import { FleetPage } from './pages/FleetPage';
import { HistoryPage } from './pages/HistoryPage';
import { HelpPage } from './pages/HelpPage';
import { MainLayout } from './layouts/MainLayout';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { index: true, element: <LivePage /> },
      { path: 'fleet', element: <FleetPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'help', element: <HelpPage /> },
    ],
  },
]);
