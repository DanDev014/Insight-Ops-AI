import { request } from "~~/server/utils/request";

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const response = await request("/login", {
    method: "POST",
    body,
  });

  return response;
});
