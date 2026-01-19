import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface HealthResponse {
  status: string;
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: async (): Promise<HealthResponse> => {
      const response = await axios.get("/api/v1/health");
      return response.data;
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading dashboard</div>;

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            ForgeX Takeoffs
          </h2>
          <p className="text-gray-600 mb-4">
            Upload construction plans and let AI generate accurate takeoffs
          </p>
          <div className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
            API Status: {data?.status || "Unknown"}
          </div>
        </div>
      </div>
    </div>
  );
}
