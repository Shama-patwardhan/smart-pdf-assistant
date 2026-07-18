import { createBrowserRouter } from "react-router-dom"
import { Workspace } from "../pages/Workspace"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Workspace />,
  },
  /* 
   * Placeholder routes for future scalable expansion:
   * 
   * {
   *   path: "/analytics",
   *   element: <AnalyticsPage />,
   * },
   * {
   *   path: "/settings",
   *   element: <SettingsPage />,
   * }
   */
])
export default router
