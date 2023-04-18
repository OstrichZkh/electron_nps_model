import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { Button } from "antd";
import {
  getProjectInfoAsync,
  switchProject,
} from "../../../store/features/dataManagementSlice.ts";
import { useSelector, useDispatch } from "react-redux";

const SiderBarBox = styled.div`
  height: 100vh;
  width: 12rem;
  background-color: rgb(244, 245, 247);
  .title {
    padding-top: 1rem;
    font-size: 1.3rem;
    font-weight: 600;
    text-align: center;
    margin: 0px auto;
    font-family: "Times New Roman", Times, serif;
  }
  .git-repo {
    text-align: center;
    margin: 0.5rem auto;
    a {
      color: rgb(25, 118, 199);
      text-decoration: none;
    }
  }
  .button {
    width: 90%;
    margin: 0.2rem auto;
  }
  .recent {
    .recent-title {
      font-size: 1rem;
      padding: 0.5rem 0 0.25px 0.5rem;
      color: rgb(85, 99, 114);
      font-weight: 800;
      margin-bottom: 0.2rem;
    }
    .recent-info {
      font-size: 1rem;
      padding: 0.6rem;
      margin: 0 0.25rem;
      border-top: 0.05rem solid rgb(222, 226, 230);
      cursor: pointer;

      color: rgb(42, 128, 202);
      text-decoration: none;

      &:hover {
        color: red;
      }
    }
  }
`;

// function SiderBar(props: any) {
//   const toRepos = function () {};
//   let [projectUpdated, setProjectUpdated] = useState(0);
//   let [projectInfos, setProjectInfos] = useState([]);

//   // 新建项目
//   const createProject = async function () {
//     const filePath = await window.electronAPI.createNewProject();
//     setProjectUpdated((prev) => prev + 1);
//   };
//   // 监听项目变化
//   useEffect(() => {
//     (async function fn() {
//       let res = await window.electronAPI.requireProjectInfo();
//       setProjectInfos(res);
//       props.setCurProjectInfo(res[0]);
//     })();
//   }, [projectUpdated]);
//   // 更换项目
//   const switchProject = function (name: string) {
//     // e.preventDefault();
//     let project: object = projectInfos.filter(
//       (info) => info.projectName == name
//     )[0];
//     props.setCurProjectInfo({ ...project });
//   };

//   return (
//     <SiderBarBox>
//       <div className="title">KH-MODEL V1.1</div>
//       <div className="git-repo">
//         <a
//           onClick={toRepos}
//           href="https://github.com/OstrichZkh/electron_nps_model"
//         >
//           点击此处
//         </a>
//         跳转到GIT仓库
//       </div>
//       <div className="button">
//         <Button block={true} type="primary" onClick={createProject}>
//           新建项目
//         </Button>
//       </div>
//       <div className="recent">
//         <div className="recent-title">最近打开项目</div>
//         {projectInfos &&
//           projectInfos.map((info: any) => {
//             return (
//               <div key={info.lastSaved} className="recent-info">
//                 <span
//                   onClick={() => {
//                     switchProject(info.projectName);
//                   }}
//                 >
//                   {info.projectName}
//                 </span>
//               </div>
//             );
//           })}
//       </div>
//     </SiderBarBox>
//   );
// }

function SiderBar(props: any) {
  // 获取公共状态
  let { allProjectInfos, curProjectInfo } = useSelector(
    (state) => state.dataManagementReducer
  );
  let dispatch = useDispatch();
  const toRepos = function () {};
  // 新建项目
  const createProject = async function () {
    const filePath = await window.electronAPI.createNewProject();
    dispatch(getProjectInfoAsync());
  };
  // 更换项目
  const switchProject_ = function (name: string) {
    dispatch(switchProject({ name: name }));
  };

  return (
    <SiderBarBox>
      <div className="title">KH-MODEL V1.1</div>
      <div className="git-repo">
        <a
          onClick={toRepos}
          href="https://github.com/OstrichZkh/electron_nps_model"
        >
          点击此处
        </a>
        跳转到GIT仓库
      </div>
      <div className="button">
        <Button block={true} type="primary" onClick={createProject}>
          新建项目
        </Button>
      </div>
      <div className="recent">
        <div className="recent-title">最近打开项目</div>
        {allProjectInfos &&
          allProjectInfos.map((info: any) => {
            return (
              <div key={info.lastSaved} className="recent-info">
                <span
                  onClick={() => {
                    switchProject_(info.projectName);
                  }}
                >
                  {info.projectName}
                </span>
              </div>
            );
          })}
      </div>
    </SiderBarBox>
  );
}
export default React.memo(SiderBar);
