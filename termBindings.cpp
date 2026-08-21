#include <pybind11/pybind11.h>

#include <string>
#include <utility>

#include "TerminalSession.h"

namespace py = pybind11;

PYBIND11_MODULE(termCore, m)
{
    m.doc() = "Sagittarius A ConPTY terminal backend";

    py::class_<TerminalSession>(m, "TerminalSession")
        .def(py::init<>())

        .def("start", &TerminalSession::Start)

        .def("stop", &TerminalSession::Stop)

        .def("is_running", &TerminalSession::IsRunning)

        .def(
            "send",
            [](TerminalSession& self, py::bytes Data)
            {
                std::string Bytes = Data;

                return self.Send(
                    Bytes.data(),
                    Bytes.size()
                );
            }
        )

        .def("resize",
            &TerminalSession::Resize)

        .def(
            "set_output_callback",
            [](TerminalSession& self, py::function Callback)
            {
                // ReaderLoop runs on a native C++ thread, so the GIL
                // must be acquired before calling Python.
                self.SetOutputCallback(
                    [Callback = std::move(Callback)]
                    (const char* Data, std::size_t Size)
                    {
                        py::gil_scoped_acquire GIL;

                        try
                        {
                            Callback(py::bytes(Data, Size));
                        }
                        catch (py::error_already_set& Error)
                        {
                            Error.discard_as_unraisable(
                                "TerminalSession output callback"
                            );
                        }
                    }
                );
            }
        );
}