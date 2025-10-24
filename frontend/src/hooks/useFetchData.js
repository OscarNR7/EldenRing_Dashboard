import { useState, useCallback } from 'react';

const useFetchData = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (serviceFunction, params) => {
    setLoading(true);
    setError(null);
    try {
      const result = await serviceFunction(params);
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, setData, loading, error, execute };
};

export default useFetchData;
