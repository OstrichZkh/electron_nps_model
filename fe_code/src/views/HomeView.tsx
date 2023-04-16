import React from "react";
import ProjectView from "./ProjectView";
import { Link, Routes, Route } from "react-router-dom";
import styled from "styled-components";
import { url } from "inspector";

const HomeViewBox = styled.div`
  .nav-box {
    background-color: red;
    height: 100vh;
    width: 3rem;
    .file-box {
      width: 40px;
      height: 40px;
      background-color: green;
      background-image: url("../assets/svgs/file-actived.svg");
    }
  }
`;

function HomeView() {
  return (
    <HomeViewBox>
      <div className="nav-box">
        <Link to="/">
          <img className="file-box"></img>
        </Link>
        <div>1</div>
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
