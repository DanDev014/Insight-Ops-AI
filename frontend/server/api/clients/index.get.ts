import { authRequest } from "~~/server/utils/authRequest";

export default defineEventHandler(async (event) => {
  const query = getQuery(event);

  return await authRequest(event, (user) => ({
    endpoint: `/clients/${user.id}`,
    options: { method: "GET", query },
  }));
});