import { authRequest } from "~~/server/utils/authRequest";

export default defineEventHandler(async (event) => {
  const body = await readBody(event);

  return await authRequest(event, (user) => ({
    endpoint: "/projects",
    options: {
      method: "POST",
      body: { ...body, user_id: user.id },
    },
  }));
});
