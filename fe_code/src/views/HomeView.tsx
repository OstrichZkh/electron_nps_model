import React, { useEffect, useState } from "react";
import ProjectView from "./ProjectView";
import SetupView from "./SetupView";

import { Link } from "react-router-dom";
import styled from "styled-components";
import { ReactSVG } from "react-svg";
import activeFile from "../assets/svgs/file-actived.svg";
import unactiveFile from "../assets/svgs/file-unactive.svg";
import activeSetup from "../assets/svgs/setup-actived.svg";
import unactiveSetup from "../assets/svgs/setup-unactive.svg";
import RouterView from "../router";

const HomeViewBox = styled.div`
  display: flex;
  flex-direction: row;
  .nav-box {
    background-color: rgb(18, 60, 105);
    width: 4rem;
    .nav-box-inner {
      position: fixed;
      background-color: rgb(18, 60, 105);
      width: 4rem;
      height: 100vh;
    }
    .file-box {
      width: 3rem;
      height: 3rem;
      margin: 0.4rem auto;

      svg {
        width: 3rem;
        height: 3rem;
      }
    }
  }
`;

function HomeView() {
  let [curPage, setCurPage] = useState("project");
  let changeTab = function (tab: "project" | "setup"): void {
    setCurPage(tab);
  };

  return (
    <HomeViewBox>
      <div className="nav-box">
        <div className="nav-box-inner">
          <Link to="/">
            <div
              className="file-box"
              onClick={() => {
                changeTab("project");
              }}
            >
              <ReactSVG
                src={curPage == "project" ? activeFile : unactiveFile}
              />
            </div>
          </Link>
          <Link
            to="/setup"
            onClick={() => {
              changeTab("setup");
            }}
          >
            <div className="file-box">
              <ReactSVG
                src={curPage !== "project" ? activeSetup : unactiveSetup}
              />
            </div>
          </Link>
        </div>
      </div>

      <div className="page-box">
        <RouterView />
      </div>

      {/* <Link to="/">项目管理</Link>
        <Link to="/data">数据管理</Link>
        <Routes>
          <Route path="/" element={<ProjectView />}></Route>
        </Routes> */}
    </HomeViewBox>
  );
}

export default HomeView;
