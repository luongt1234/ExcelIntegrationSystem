import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import { AppProvider } from './contexts/AppContext';
import Login from './pages/Login';
import Home from './pages/Home';
import PeopleMerge from './pages/PeopleMerge';
import InfoAppend from './pages/InfoAppend';
import GoodsMerge from './pages/GoodsMerge';
import DynamicPivot from './pages/DynamicPivot';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
};

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/home" element={<Home />} />
                  <Route path="/" element={<Navigate to="/home" replace />} />
                  <Route path="/people-merge" element={<PeopleMerge />} />
                  <Route path="/info-append" element={<InfoAppend />} />
                  <Route path="/goods-merge" element={<GoodsMerge />} />
                  <Route path="/dynamic-pivot" element={<DynamicPivot />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </Router>
    </AppProvider>
  );
}

export default App;
