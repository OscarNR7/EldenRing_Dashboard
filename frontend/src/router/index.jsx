import { createBrowserRouter } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import DashboardPage from '../pages/public/DashboardPage';
import ExploreWeaponsPage from '../pages/public/ExploreWeaponsPage';
import ExploreBossesPage from '../pages/public/ExploreBossesPage';
import ExploreArmorsPage from '../pages/public/ExploreArmorsPage';
import ExploreClassesPage from '../pages/public/ExploreClassesPage';
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
        path: 'weapons',
        element: <ExploreWeaponsPage />,
      },
      {
        path: 'bosses',
        element: <ExploreBossesPage />,
      },
      {
        path: 'armors',
        element: <ExploreArmorsPage />,
      },
      {
        path: 'classes',
        element: <ExploreClassesPage />,
      },
      // Aquí se añadirán más rutas para otras secciones
    ],
  },
]);

export default router;