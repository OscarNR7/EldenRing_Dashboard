import { createBrowserRouter } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import DashboardPage from '../pages/public/DashboardPage';
import ExploreWeaponsPage from '../pages/public/ExploreWeaponsPage';
import NotFoundPage from '../pages/public/NotFoundPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'explore/weapons',
        element: <ExploreWeaponsPage />,
      },
      // Aquí se añadirán más rutas para otras secciones
    ],
  },
]);

export default router;
