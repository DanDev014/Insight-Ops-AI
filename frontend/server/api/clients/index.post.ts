import { authRequest } from "~~/server/utils/authRequest";

export default defineEventHandler(async (event) => {
  const body = await readBody(event);

  return await authRequest(event, (user) => ({
    endpoint: "/clients",
    options: {
      method: "POST",
      body: { ...body, user_id: user.id },
    },
  }));
});