from fastapi import FastAPI
from src.routes.generate import router as generate_router
from src.routes.sse import router as sse_router


app = FastAPI()

app.include_router(generate_router)
app.include_router(sse_router)




# from fastapi import FastAPI, HTTPException
# from fastapi.responses import FileResponse
# from src.workflow import workflow_builder
# from src.pdf_generator import generate_pdf
# from schema.app import TopicRequest

# app = FastAPI()

# try:
#     orchestrator_worker = workflow_builder()
# except Exception as e:
#     raise RuntimeError(f"Failed to build workflow: {e}")    


# @app.post("/generate")
# async def generate(req: TopicRequest):

#     try:
#         result = await orchestrator_worker.ainvoke({"topic": req.topic})

#         # adjust key based on your state
#         report = result.get("final_report", "No report generated")
#         return{
#             "topic":req.topic,
#             "report": report
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error generating report: {e}")


# @app.post("/download")

# async def download(req: TopicRequest):
#     try:

#         result = await orchestrator_worker.ainvoke({"topic": req.topic})
#         report = result.get("final_report", "")

#         if not report:
#             raise HTTPException(status_code=404, detail="Report not found")
        
#         pdf_report = await generate_pdf(report)
#         return FileResponse(pdf_report, filename="report.pdf", media_type="application/pdf")
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate PDF Please try again: {e}")

    
