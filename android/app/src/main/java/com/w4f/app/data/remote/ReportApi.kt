package com.w4f.app.data.remote

import com.w4f.app.data.remote.dto.ProjectListOutDto
import com.w4f.app.data.remote.dto.ReportDetailDto
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface ReportApi {
  @GET("reports/{id}") suspend fun getReportDetail(@Path("id") reportId: String): ReportDetailDto

  @GET("projects") suspend fun getProjects(@Query("report_id") reportId: String): ProjectListOutDto
}
