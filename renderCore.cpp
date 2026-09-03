#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <opencv2/opencv.hpp>
#include <QPainter>
#include <QPixmap>
#include <QColor>
#include <QPen>
#include <QPointF>
#include <QList>
#include <iostream>
#include <stdexcept>
#include <cmath>
#include <algorithm>
#include <limits>
#include <vector>
#include <tuple>
#include <string>

namespace py = pybind11;

void rebuildTraceMap(
    py::list& traceData,
    const py::list& mapPtrs,
    py::list& InCanvGlobIDs,
    py::list& ToAddGlobIDs,
    py::list& ToRemGlobIDs,
    const py::list& LocalSignals,
    const py::dict& GlobalSignals,
    py::array_t<float>& Axis,
    py::array_t<int>& ActivePx,
    py::array_t<int>& SampleIdxs,
    float     pixelRatio,
    int       width,
    int       height,
    float     xmin,
    float     xmax,
    float     axisStart,
    float     axisStop,
    float     AxisCoveredPerPx,
    float     yAvg,
    float     yRange,
    int       prevIdx,
    int       postIdx
) {
    auto axisBuf = Axis.request();
    float* axis  = static_cast<float*>(axisBuf.ptr);

    auto pxBuf               = ActivePx.request();
    int* activePx            = static_cast<int*>(pxBuf.ptr);
    size_t reserveSize       = pxBuf.size + 2;
    const size_t activeCount = pxBuf.size;

    auto idxBuf     = SampleIdxs.request();
    int* sampleIdxs = static_cast<int*>(idxBuf.ptr);

    traceData    .clear();
    InCanvGlobIDs.clear();
    ToAddGlobIDs .clear();
    ToRemGlobIDs .clear();

    size_t totalSignals = LocalSignals.size();
    for (size_t i = 0; i < totalSignals; ++i) {
        InCanvGlobIDs.append(0);
    }

    int idx = 0;
    for(auto item_handle : LocalSignals) {
        py::object item = py::reinterpret_borrow<py::object>(item_handle);
        int globalID    = item.attr("Global_ID").cast<int>();
        int localID     = item.attr("Local_ID").cast<int>();
        float linewidth = item.attr("Width").cast<float>();

        if (!GlobalSignals.contains(globalID)) {
            throw std::runtime_error("Global ID " + std::to_string(globalID) + " not found in GlobalSignals dictionary.");
        }

        py::object globalSignal = GlobalSignals[py::cast(globalID)].cast<py::object>();

        py::object pyColor = globalSignal.attr("color");
        int r = pyColor.attr("red")().cast<int>();
        int g = pyColor.attr("green")().cast<int>();
        int b = pyColor.attr("blue")().cast<int>();
        int a = pyColor.attr("alpha")().cast<int>();
        QColor color(r, g, b, a);

        py::array_t<float> Trace = globalSignal.attr("data").cast<py::array_t<float>>();
        auto traceBuf            = Trace.request();
        float* trace             = static_cast<float*>(traceBuf.ptr);

        uintptr_t addr = mapPtrs[idx].cast<uintptr_t>();
        QPixmap* map = reinterpret_cast<QPixmap*>(addr);

        QPainter painter(map);
        painter.setRenderHint(QPainter::Antialiasing, false);

        QPen thinPen (color, linewidth/2);
        QPen thickPen(color, linewidth  );

        painter.setPen(thinPen);

        std::vector<int>   centerX;
        std::vector<float> centerY;
        std::vector<float> min    ;
        std::vector<float> max    ;

        centerX.reserve(reserveSize);
        centerY.reserve(reserveSize);
        min    .reserve(reserveSize);
        max    .reserve(reserveSize);

        if (xmin > axisStart && prevIdx >= 0 && prevIdx < Axis.size()){
            float prevXPx = (axis[prevIdx] - xmin) / AxisCoveredPerPx;
            float prevYPx = (yAvg + yRange / 2 - trace[prevIdx]) * height / yRange;
            centerX.push_back(int(prevXPx));
            centerY.push_back(   prevYPx  );
            min    .push_back(   prevYPx  );
            max    .push_back(   prevYPx  );
        }

        for (size_t i = 0; i < activeCount; i++) {
            int px = activePx[i];
            int leftIndex  = sampleIdxs[px];
            int rightIndex = sampleIdxs[px + 1];
            auto [minSample, MaxSample] = std::minmax_element(trace + leftIndex, trace + rightIndex);
            float pxYmax = (yAvg + yRange / 2 - *minSample) * height / yRange;
            float pxYmin = (yAvg + yRange / 2 - *MaxSample) * height / yRange;
            float pxYctr = (pxYmax + pxYmin) / 2;

            if (((pxYmax - pxYmin) / height) <= 0.02) {
                pxYmin = pxYctr;
                pxYmax = pxYctr;
            }
            else {
                painter.drawLine(
                    px, pxYmin,
                    px, pxYmax
                );
            }

            centerX.push_back(  px  );
            centerY.push_back(pxYctr);
            min    .push_back(pxYmin);
            max    .push_back(pxYmax);
        }

        if (xmax < axisStop && postIdx >= 0 && postIdx < Axis.size()){
            float postXPx = (axis[postIdx] - xmin) / AxisCoveredPerPx;
            float postYPx = (yAvg + yRange / 2 - trace[postIdx]) * height / yRange;
            centerX.push_back(int(postXPx));
            centerY.push_back(   postYPx  );
            min    .push_back(   postYPx  );
            max    .push_back(   postYPx  );
        }

        painter.setRenderHint(QPainter::Antialiasing, false);
        painter.setPen(thickPen);

        QList<QPointF> points;
        points.reserve(centerX.size());
        for (size_t i = 0; i < centerX.size(); ++i) {
            points.append(QPointF(centerX[i], centerY[i]));
        }
        painter.drawPolyline(points);

        painter.setRenderHint(QPainter::Antialiasing, true);
        painter.end();

        py::dict traceinfo;

        traceinfo["Global_ID"] = globalID;
        traceinfo["Local_ID"]  = localID;
        traceinfo["CentrX"]    = centerX;
        traceinfo["CentrY"]    = centerY;
        traceinfo["MinY"]      = min;
        traceinfo["MaxY"]      = max;
        traceinfo["color"]     = py::make_tuple(r, g, b, a);

        traceData.append(traceinfo);
        InCanvGlobIDs[localID] = py::int_(globalID);

        idx += 1;
    }

    return;
}

template <typename T>
void fill_matrix(const py::buffer_info& buf, T value) {
    T* ptr = static_cast<T*>(buf.ptr);
    size_t rows = buf.shape[0];
    size_t cols = buf.shape[1];
    size_t r_stride = buf.strides[0] / sizeof(T);
    size_t c_stride = buf.strides[1] / sizeof(T);

    for (size_t r = 0; r < rows; ++r) {
        for (size_t c = 0; c < cols; ++c) {
            ptr[r * r_stride + c * c_stride] = value;
        }
    }
}

std::tuple<py::array_t<int32_t>, py::array_t<double>, py::array_t<double>> 
hitRebuild(
    py::array_t<int32_t> field_mat,
    py::array_t<double> trace_mat,   // Changed to double array for y-coordinates
    py::array_t<double> point_mat,
    py::list trace_data,
    int canvas_h, int canvas_w, int highlight_width
) {
    size_t num_traces = trace_data.size();

    // 1. Sync shapes and reset buffers
    bool field_match = (field_mat.ndim() == 2 && field_mat.shape(0) == canvas_h && field_mat.shape(1) == canvas_w);
    bool point_match = (point_mat.ndim() == 2 && point_mat.shape(0) == canvas_h && point_mat.shape(1) == canvas_w);
    bool trace_match = (trace_mat.ndim() == 2 && trace_mat.shape(0) == num_traces && trace_mat.shape(1) == canvas_w);

    // Reallocate field_mat if shape changed
    if (!field_match) {
        field_mat = py::array_t<int32_t>({canvas_h, canvas_w});
    }
    py::buffer_info field_buf = field_mat.request();
    fill_matrix<int32_t>(field_buf, -1);

    // Reallocate point_mat if shape changed
    if (!point_match) {
        point_mat = py::array_t<double>({canvas_h, canvas_w});
    }
    py::buffer_info point_buf = point_mat.request();
    fill_matrix<double>(point_buf, -1.0);

    // Reallocate trace_mat if shape changed (Shape: [num_traces, canvas_w])
    if (!trace_match) {
        trace_mat = py::array_t<double>({
            static_cast<py::ssize_t>(num_traces), 
            static_cast<py::ssize_t>(canvas_w)
        });
    }
    py::buffer_info trace_buf = trace_mat.request();
    fill_matrix<double>(trace_buf, -1.0);

    // Get direct raw pointers
    int32_t* field_ptr = static_cast<int32_t*>(field_buf.ptr);
    double* point_ptr = static_cast<double*>(point_buf.ptr);
    double* trace_ptr = static_cast<double*>(trace_buf.ptr);

    // Calculate element strides
    size_t f_r_stride = field_buf.strides[0] / sizeof(int32_t);
    size_t f_c_stride = field_buf.strides[1] / sizeof(int32_t);
    
    size_t p_r_stride = point_buf.strides[0] / sizeof(double);
    size_t p_c_stride = point_buf.strides[1] / sizeof(double);

    size_t t_r_stride = trace_buf.strides[0] / sizeof(double); // Row stride (Trace Index)
    size_t t_c_stride = trace_buf.strides[1] / sizeof(double); // Col stride (X position)

    // 2. OpenCV Wrapper Setup
    cv::Mat cv_field;
    bool openCvCompatible = (f_c_stride == 1);
    
    if (openCvCompatible) {
        cv_field = cv::Mat(canvas_h, canvas_w, CV_32SC1, field_ptr, field_buf.strides[0]);
    } else {
        cv_field = cv::Mat::zeros(canvas_h, canvas_w, CV_32SC1);
    }

    // 3. Process Traces
    for (size_t t = 0; t < num_traces; ++t) {
        py::dict trace = trace_data[t].cast<py::dict>();
        int local_id = trace["Local_ID"].cast<int>();
        std::vector<double> trcCentrX = trace["CentrX"].cast<std::vector<double>>();
        std::vector<double> trcCentrY = trace["CentrY"].cast<std::vector<double>>();
        std::vector<double> trcMin = trace["MinY"].cast<std::vector<double>>();
        std::vector<double> trcMax = trace["MaxY"].cast<std::vector<double>>();

        if (trcCentrX.empty()) continue;

        // Step A: Draw Polylines
        std::vector<cv::Point> pts;
        pts.reserve(trcCentrX.size());
        for (size_t i = 0; i < trcCentrX.size(); ++i) {
            pts.push_back(cv::Point(static_cast<int>(trcCentrX[i]), static_cast<int>(trcCentrY[i])));
        }
        
        std::vector<std::vector<cv::Point>> pp{pts};
        cv::polylines(
            cv_field,
            pp,
            false,
            cv::Scalar(local_id),
            highlight_width,
            cv::LINE_8
        );

        if (!openCvCompatible) {
            for (const auto& pt : pts) {
                if (pt.y >= 0 && pt.y < canvas_h && pt.x >= 0 && pt.x < canvas_w) {
                    field_ptr[pt.y * f_r_stride + pt.x * f_c_stride] = local_id;
                }
            }
        }

        // Step B: Interpolate & Fill TraceMatrix + PointMatrix
        for (size_t i = 0; i < trcCentrX.size(); ++i) {
            double center = trcCentrX[i];

            if (i + 1 < trcCentrX.size()) {
                double nextCenter = trcCentrX[i + 1];
                if (static_cast<int>(nextCenter) == static_cast<int>(center)) continue;

                int start_x = static_cast<int>(center);
                int end_x = static_cast<int>(nextCenter);
                double dx = nextCenter - center;
                double dy = trcCentrY[i + 1] - trcCentrY[i];

                for (int x = start_x; x < end_x; ++x) {
                    if (x >= canvas_w || x < 0) continue;
                    
                    double y = (x - center) * dy / dx + trcCentrY[i];

                    // 1. Store interpolated Y directly into TraceMatrix for Trace t at Column x
                    trace_ptr[t * t_r_stride + x * t_c_stride] = y;

                    // 2. Fill PointMatrix where field_mat matches local_id
                    for (int r = 0; r < canvas_h; ++r) {
                        int32_t current_val = openCvCompatible ? 
                                              field_ptr[r * f_r_stride + x * f_c_stride] : 
                                              cv_field.at<int32_t>(r, x);

                        if (current_val == local_id) {
                            point_ptr[r * p_r_stride + x * p_c_stride] = y;
                        }
                    }
                }
            }

            // Step C: Draw vertical indicator line
            cv::line(
                cv_field,   
                cv::Point(static_cast<int>(center), static_cast<int>(trcMin[i])),
                cv::Point(static_cast<int>(center), static_cast<int>(trcMax[i])),
                cv::Scalar(local_id),
                highlight_width
            );
        }
    }

    // Direct writeback if fallback was used
    if (!openCvCompatible) {
        for (int r = 0; r < canvas_h; ++r) {
            for (int c = 0; c < canvas_w; ++c) {
                field_ptr[r * f_r_stride + c * f_c_stride] = cv_field.at<int32_t>(r, c);
            }
        }
    }

    return std::make_tuple(field_mat, trace_mat, point_mat);
}

PYBIND11_MODULE(renderCore, m) {
    m.doc() = "milky blueberry pie";
    m.def("rebuildTraceMap", &rebuildTraceMap, "jupiter");
    m.def("hitRebuild", &hitRebuild, "mars");
}